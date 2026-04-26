from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.core.paginator import Paginator
from django.http import JsonResponse

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from accounts.forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from .models import RestaurantProfile, MenuCategory, FoodCategory, FoodItem, Offer, Day
from .forms import RestaurantProfileForm, MenuCategoryForm
from users.models import Orders
from coupons.models import Coupon


from django.db.models import Count
from django.utils.timezone import now
from django.db.models import Case, Count, IntegerField, Prefetch, Q, Sum, Value, When
from django.utils.timezone import localtime
from datetime import datetime
from accounts.models import CustomUser, UserProfile, RestaurantImage
from accounts.utils import get_location_from_point
from .models import Subscriptions, RestaurantTransaction
from .forms import FoodItemManageForm, MenuManageForm, FoodCategoryManageForm, OfferForm

import logging

logger = logging.getLogger("myapp")


def _handle_view_error(request, view_name, redirect_name="restaurant-home"):
    logger.exception("Error in %s", view_name)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
        return JsonResponse(
            {"success": False, "error": "Something went wrong. Please try again."},
            status=500,
        )
    messages.error(request, "Something went wrong. Please try again.")
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect(redirect_name)


def redirect_with_get_params(request, url_name):
    base_url = reverse(url_name)
    query_string = request.META.get("QUERY_STRING", "")
    if query_string:
        return redirect(f"{base_url}?{query_string}")
    return redirect(base_url)


def _next_url(request):
    return request.POST.get("next") or request.GET.get("next")


def _redirect_to_next_or_default(request, default_url_name):
    next_url = _next_url(request)
    if next_url:
        return redirect(next_url)
    return redirect(default_url_name)


def _form_errors_as_text(form):
    errors = []
    for field_name, field_errors in form.errors.items():
        for error in field_errors:
            if field_name == "__all__":
                errors.append(str(error))
            else:
                errors.append(f"{field_name}: {error}")
    return " | ".join(errors)


@login_required(login_url="login")
def home(request):
    try:
        if request.user.user_type != "restaurant":
            messages.error(request, "Not restaurant user")
            return redirect("login")
    
    
        restaurant = get_object_or_404(RestaurantProfile, user=request.user)
    
        date_str = request.GET.get("date")
        try:
            selected_date = (
                datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else now().date()
            )
        except ValueError:
            selected_date = now().date()
    
        # Total orders per food category for today
        food_category_orders = (
            Orders.objects.filter(delivery_date=selected_date, restaurant=restaurant)
            .values("food_category__name")
            .annotate(total_orders=Count("id"))
            .order_by("food_category__name")
        )
        # Cancelled orders per food category for today
        cancelled_orders = (
            Orders.objects.filter(
                delivery_date=selected_date, restaurant=restaurant, status="CANCELLED"
            )
            .values("food_category__name")
            .annotate(cancelled_orders=Count("id"))
            .order_by("food_category__name")
        )
        # Merge both querysets into a single list of dicts
        data = {}
        for item in food_category_orders:
            name = item["food_category__name"] or "Unknown"
            data[name] = {
                "category": name,
                "total_orders": item["total_orders"],
                "cancelled_orders": 0,
            }
        for item in cancelled_orders:
            name = item["food_category__name"] or "Unknown"
            if name in data:
                data[name]["cancelled_orders"] = item["cancelled_orders"]
            else:
                data[name] = {
                    "category": name,
                    "total_orders": 0,
                    "cancelled_orders": item["cancelled_orders"],
                }
    
        context = {
            "dashboard_data": data.values(),
            "restaurant": restaurant,
            "selected_date": selected_date,
        }
        return render(request, "./restaurant/dashboard.html", context)
    except Exception:
        return _handle_view_error(request, "home")


@login_required(login_url="login")
def restaurant_logout(request):
    try:
        logout(request)
        request.session.flush()
        return redirect("login")
    except Exception:
        return _handle_view_error(request, "restaurant_logout")


@login_required(login_url="login")
def restaurant_register(request, editing=None):

    try:
        if RestaurantProfile.objects.filter(user=request.user, is_approved=True).exists():
            messages.success(request, "Manage your restaurant")
            return redirect("restaurant-home")
        try:
            restaurant = RestaurantProfile.objects.get(user=request.user, is_approved=False)
        except RestaurantProfile.DoesNotExist:
            restaurant = None
    
        if restaurant and editing is None:
            return render(
                request,
                "./restaurant/registration_success.html",
                {"restaurant_registration": True, "restaurant": restaurant},
            )
    
        if request.method == "POST":
            form = RestaurantProfileForm(request.POST, request.FILES, instance=restaurant)
            if form.is_valid():
                restaurant = form.save(commit=False)
                restaurant.user_type = "restaurant"
                restaurant.user = request.user
                restaurant.is_approved = True
                if editing:
                    new_comment = "Request edited"
                    if new_comment:
                        existing_comments = restaurant.admin_comments or ""
                        restaurant.admin_comments = (
                            f"{existing_comments}\n{new_comment}"
                            if existing_comments
                            else new_comment
                        )
    
                restaurant.save()
                request.user.user_type = "restaurant"
                request.user.save()
                name = form.cleaned_data.get("restaurant_name")
                # messages.success(request, f"Restaurant request sent")
                return redirect("restaurant-register")
            else:
                messages.error(request, "Invalid inputs.")
        else:
            form = RestaurantProfileForm(instance=restaurant)
    
        context = {"form": form, "restaurant": restaurant, "restaurant_registration": True}
    
        return render(request, "./restaurant/restaurant-register.html", context)
    except Exception:
        return _handle_view_error(request, "restaurant_register")


@login_required(login_url="login")
def profile(request):
    try:
        restaurant = get_object_or_404(RestaurantProfile, user=request.user)

        # Backfill missing display location for existing records.
        if not restaurant.location_name and restaurant.point:
            location_name = get_location_from_point(restaurant.point.x, restaurant.point.y)
            if location_name:
                restaurant.location_name = location_name
                restaurant.save(update_fields=["location_name"])
    
        if request.method == "POST":
            form = RestaurantProfileForm(request.POST, request.FILES, instance=restaurant)
            if form.is_valid():
                restaurant = form.save(commit=False)
                restaurant.user_type = "restaurant"
                restaurant.user = request.user
                restaurant.is_approved = True
                restaurant.save()
                messages.success(request, "Restaurant profile updated.")
                return redirect("restaurant-profile")
            else:
                messages.error(request, "Invalid inputs.")
        else:
            form = RestaurantProfileForm(instance=restaurant)
    
        context = {"form": form, "restaurant_obj": restaurant}
    
        upload = request.GET.get("upload")
        if upload == "image":
            context.update({"page": "image"})
        return render(request, "./restaurant/restaurant-profile.html", context)
    except Exception:
        return _handle_view_error(request, "profile")


# Menu Category Views


@login_required(login_url="login")
def menu_category_list(request):
    # Assuming the user is logged in and has a restaurant profile
    restaurant = request.user.restaurantprofile
    menu_categories = MenuCategory.objects.filter(restaurant=restaurant)
    context = {
        "menu_categories": menu_categories,
    }
    return render(request, "restaurant/menu.html", context)


@login_required(login_url="login")
def menu_category_add(request):
    restaurant = RestaurantProfile.objects.get(user=request.user)
    if request.method == "POST":
        form = MenuCategoryForm(request.POST)
        if form.is_valid():
            if MenuCategory.objects.filter(
                restaurant=restaurant, name=form.cleaned_data.get("name")
            ).exists():
                messages.error(
                    request,
                    f"A category with the name already exists for this restaurant.",
                )
                return redirect("menu_category_add")
            menu_category = form.save(commit=False)
            menu_category.restaurant = restaurant
            menu_category.save()
            return redirect("menu_category_list")
    else:
        form = MenuCategoryForm()

    return render(request, "restaurant/add_menu_category.html", {"form": form})


@login_required(login_url="login")
def menu_category_edit(request, pk):
    menu_category = get_object_or_404(MenuCategory, pk=pk)
    if request.method == "POST":
        form = MenuCategoryForm(request.POST, instance=menu_category)
        if form.is_valid():
            form.save()
            messages.success(request, "Menu category updated successfully!")
            return redirect("menu_category_list")
    else:
        form = MenuCategoryForm(instance=menu_category)

    return render(
        request, "restaurant/add_menu_category.html", {"form": form, "action": "Edit"}
    )


@login_required(login_url="login")
def menu_category_delete(request, pk):
    menu_category = get_object_or_404(MenuCategory, pk=pk)
    if menu_category:
        menu_category.delete()
        messages.success(request, "Menu category deleted successfully!")
        return redirect("menu_category_list")

    return render(request, "restaurant/menu.html")


# Food Category Views


@login_required(login_url="login")
def food_category_list(request):
    restaurant = request.user.restaurantprofile
    food_categories = FoodCategory.objects.filter(restaurant=restaurant)
    return render(
        request,
        "restaurant/food_category_list.html",
        {"food_categories": food_categories},
    )


def users(request):
    try:
        if request.user.user_type != "restaurant":
            messages.error(request, "Not restaurant user")
            return redirect("login")
        restaurant = get_object_or_404(RestaurantProfile, user=request.user)
        subscriptions = Subscriptions.objects.filter(
            restaurant=restaurant, user__isnull=False
        )
        paginator = Paginator(subscriptions, 10)  # Show 10 users per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    
        context = {"page_obj": page_obj}
        return render(request, "./restaurant/all_users.html", context)
    except Exception:
        return _handle_view_error(request, "users")


@login_required(login_url="admin-login")
def orders(request):
    try:
        print(request.GET)
    
        user = request.user
        restaurant = get_object_or_404(RestaurantProfile, user=request.user)
        sort_by = request.GET.get("sort", "delivery_date")  # default: delivery_date
        direction = request.GET.get("dir", "asc")
        order_prefix = "" if direction == "asc" else "-"
        valid_sort_fields = ["delivery_date", "status"]
        sort_field = sort_by if sort_by in valid_sort_fields else "delivery_date"
        orders = Orders.objects.filter(restaurant=restaurant).order_by(
            f"{order_prefix}{sort_field}"
        )
        user = request.GET.get("user")
        status = request.GET.get("status")
        delivery_date = request.GET.get("delivery_date")
    
        if user:
            orders = orders.filter(user__username__icontains=user)
    
        if status:
            orders = orders.filter(status=status)
    
        if delivery_date:
            orders = orders.filter(delivery_date=delivery_date)
    
        paginator = Paginator(orders, 10)  # Show 5 orders per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    
        context = {
            "orders": page_obj,
            "sort": sort_field,
            "dir": direction,
        }
        return render(request, "./restaurant/orders.html", context)
    except Exception:
        return _handle_view_error(request, "orders")


@login_required
def cancel_order(request, order_id):
    try:
        order = get_object_or_404(Orders, id=order_id)

        if order.cancel():
            messages.success(request, f"Order cancelled successfully")
        else:
            messages.error(request, "Order cannot be cancelled.")
    except Exception as e:
        logger.error(f"{e=}")
        messages.error(request, "Server error")
    finally:
        return redirect_with_get_params(request, "restaurant-orders")


@login_required
def deliver_order(request, order_id):
    try:
        print(request.GET)
        try:
            order = get_object_or_404(Orders, id=order_id)
            # Prevent marking as delivered before the delivery date
            if order.delivery_date > timezone.now().date():
                messages.error(request, "Cannot mark as delivered before delivery date.")
                return redirect_with_get_params(request, "restaurant-orders")
    
            # Mark current order as delivered
            order.status = "DELIVERED"
            order.save()
            subscription = order.subscription_id
            if subscription:
                logger.info(f"Checking subscription #{subscription.id} for deactivation")
                # Check if subscription period has ended
                logger.info(f"{subscription.extended_end_date.date()=}")
                logger.info(f"{timezone.now().date()=}")
    
            messages.success(request, f"Order Delivered")
    
        except Exception as e:
            logger.error(f"{e=}")
            messages.error(request, "Server error")
    
        finally:
            return redirect_with_get_params(request, "restaurant-orders")
    except Exception:
        return _handle_view_error(request, "deliver_order")


@login_required(login_url="login")
def foods(request):

    try:
        if request.user.user_type != "restaurant":
            messages.error(request, "Not restaurant user")
            return redirect("login")
    
        user = request.user
        restaurant = get_object_or_404(RestaurantProfile, user=request.user)
        foods = FoodItem.objects.filter(restaurant=restaurant).order_by("-created_at")
        paginator = Paginator(foods, 10)  # Show 5 orders per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    
        context = {"foods": page_obj, "orders": page_obj}
        return render(request, "./restaurant/food_items.html", context)
    except Exception:
        return _handle_view_error(request, "foods")


@login_required()
def food_add_or_update(request, pk=None):
    try:
        if request.user.user_type != "restaurant":
            messages.error(request, "Not restaurant user")
            return redirect("login")
    
        restaurant_obj = get_object_or_404(RestaurantProfile, user=request.user)
        food_obj = (
            get_object_or_404(FoodItem, pk=pk, restaurant=restaurant_obj) if pk else None
        )
    
        if request.method == "POST":
            form = FoodItemManageForm(
                request.POST, request.FILES, instance=food_obj, restaurant=restaurant_obj
            )
            if form.is_valid():
                food_item = form.save(commit=False)
                food_item.restaurant = restaurant_obj
                food_item.menu_category = (
                    food_item.food_category.menu_category
                    if food_item.food_category
                    else None
                )
                food_item.save()
                form.save_m2m()  # Save ManyToMany (available_days)
                messages.success(request, f"Food {'Updated' if pk else 'Created'}")
                next_url = _next_url(request)
                if next_url:
                    return redirect(next_url)
                return redirect("restaurant-food_items-edit", food_item.pk)
            else:
                messages.error(request, "Invalid inputs.")
                error_text = _form_errors_as_text(form)
                if error_text:
                    messages.error(request, error_text)
                logger.error(form.errors)
                if _next_url(request):
                    return _redirect_to_next_or_default(request, "restaurant-menu_items")
        else:
            form = FoodItemManageForm(instance=food_obj, restaurant=restaurant_obj)
    
        return render(request, "./restaurant/add-food.html", {"form": form})
    except Exception:
        return _handle_view_error(request, "food_add_or_update")


@login_required(login_url="login")
def delete_food_item(request, id):
    try:
        if request.user.user_type != "restaurant":
            messages.error(request, "Not restaurant user")
            return redirect("login")
        restaurant_obj = get_object_or_404(RestaurantProfile, user=request.user)
        food = get_object_or_404(FoodItem, pk=id, restaurant=restaurant_obj)
        food.delete()
        messages.success(request, "Food deleted.")
        return _redirect_to_next_or_default(request, "restaurant-menu_items")
    except Exception:
        return _handle_view_error(request, "delete_food_item")


@login_required(login_url="login")
def menus(request):
    try:
        if request.user.user_type != "restaurant":
            messages.error(request, "Not restaurant user")
            return redirect("login")
    
        restaurant_obj = get_object_or_404(RestaurantProfile, user=request.user)
        weekday_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        for day_name in weekday_names:
            Day.objects.get_or_create(name=day_name)
    
        weekday_order = Case(
            *[When(name=day, then=Value(index)) for index, day in enumerate(weekday_names)],
            output_field=IntegerField(),
        )
        day_options = (
            Day.objects.filter(name__in=weekday_names)
            .annotate(_weekday_order=weekday_order)
            .order_by("_weekday_order")
        )
    
        menus = MenuCategory.objects.filter(restaurant=restaurant_obj).order_by("created_at")
        selected_menu_id = request.GET.get("menu_id")
        if selected_menu_id and menus.filter(id=selected_menu_id).exists():
            selected_menu = menus.get(id=selected_menu_id)
        else:
            selected_menu = menus.first()
    
        selected_menu_categories = []
        if selected_menu:
            selected_menu_categories = (
                FoodCategory.objects.filter(
                    restaurant=restaurant_obj,
                    menu_category=selected_menu,
                )
                .prefetch_related(
                    Prefetch(
                        "food_items",
                        queryset=FoodItem.objects.filter(restaurant=restaurant_obj)
                        .select_related("food_category", "menu_category")
                        .prefetch_related("days")
                        .order_by("created_at"),
                    )
                )
                .order_by("created_at")
            )
    
        category_choices = FoodCategory.objects.filter(restaurant=restaurant_obj).order_by(
            "menu_category__name", "name"
        )
        context = {
            "menus": menus,
            "selected_menu": selected_menu,
            "selected_menu_categories": selected_menu_categories,
            "category_choices": category_choices,
            "day_options": day_options,
        }
        return render(request, "./restaurant/menu_management.html", context)
    except Exception:
        return _handle_view_error(request, "menus")


@login_required(login_url="login")
def menu_add_or_update(request, pk=None):
    try:
        restaurant_obj = get_object_or_404(RestaurantProfile, user=request.user)
        if pk:
            menu_obj = get_object_or_404(MenuCategory, pk=pk, restaurant=restaurant_obj)
        else:
            menu_obj = None

        if request.method == "POST":
            menu_post_data = request.POST.copy()
            if _next_url(request):
                # Modal submits should keep menu active by default unless explicitly toggled off.
                if "is_active" not in menu_post_data:
                    menu_post_data["is_active"] = "on"
                if pk and "description" not in menu_post_data and menu_obj:
                    menu_post_data["description"] = menu_obj.description or ""

            form = MenuManageForm(menu_post_data, request.FILES, instance=menu_obj)
            if form.is_valid():
                menu = form.save(commit=False)
                menu.restaurant = restaurant_obj
                menu.save()
                messages.success(request, f"Menu  {'Updated' if pk else 'Created'} ")
                return _redirect_to_next_or_default(request, "restaurant-menu_items")
            else:
                messages.error(request, "Invalid inputs.")
                error_text = _form_errors_as_text(form)
                if error_text:
                    messages.error(request, error_text)
                if _next_url(request):
                    return _redirect_to_next_or_default(request, "restaurant-menu_items")
        else:
            form = MenuManageForm(instance=menu_obj)

        return render(request, "./restaurant/add-menu.html", {"form": form})
    except Exception:
        return _handle_view_error(request, "menu_add_or_update")


@login_required(login_url="login")
def menu_food_item(request, id):
    try:
        restaurant_obj = get_object_or_404(RestaurantProfile, user=request.user)
        menu = get_object_or_404(MenuCategory, pk=id, restaurant=restaurant_obj)
        menu.delete()
        messages.success(request, "Menu deleted.")
        return _redirect_to_next_or_default(request, "restaurant-menu_items")
    except Exception:
        return _handle_view_error(request, "menu_food_item")


@login_required(login_url="admin-login")
def food_category(request):

    try:
        foods = FoodCategory.objects.filter(
            restaurant=request.user.restaurantprofile
        ).order_by("-created_at")
        context = {"foods": foods}
        return render(request, "./restaurant/food_categories.html", context)
    except Exception:
        return _handle_view_error(request, "food_category")


@login_required(login_url="login")
def category_add_or_update(request, pk=None):
    try:
        restaurant_obj = get_object_or_404(RestaurantProfile, user=request.user)
        if pk:
            food_obj = get_object_or_404(FoodCategory, pk=pk, restaurant=restaurant_obj)
        else:
            food_obj = None
    
        if request.method == "POST":
            form = FoodCategoryManageForm(request.POST, request.FILES, instance=food_obj)
            if form.is_valid():
                restaurant_form = form.save(commit=False)
                restaurant_form.restaurant = restaurant_obj
                restaurant_form.save()
                messages.success(request, f"Category  {'Updated' if pk else 'Created'} ")
                return _redirect_to_next_or_default(request, "restaurant-menu_items")
            else:
                messages.error(request, "Invalid inputs.")
                error_text = _form_errors_as_text(form)
                if error_text:
                    messages.error(request, error_text)
                if _next_url(request):
                    return _redirect_to_next_or_default(request, "restaurant-menu_items")
        else:
            form = FoodCategoryManageForm(instance=food_obj, restaurant=restaurant_obj)
    
        return render(request, "./restaurant/add-category.html", {"form": form})
    except Exception:
        return _handle_view_error(request, "category_add_or_update")


@login_required(login_url="login")
def delete_food_category(request, id):
    try:
        restaurant_obj = get_object_or_404(RestaurantProfile, user=request.user)
        food = get_object_or_404(FoodCategory, pk=id, restaurant=restaurant_obj)
        food.delete()
        messages.success(request, "Category deleted.")
        return _redirect_to_next_or_default(request, "restaurant-menu_items")
    except Exception:
        return _handle_view_error(request, "delete_food_category")


@login_required(login_url="login")
def offers(request):
    try:
        if request.user.user_type != "restaurant":
            messages.error(request, "Not restaurant user")
            return redirect("login")
    
        user = request.user
        restaurant = get_object_or_404(RestaurantProfile, user=request.user)
        offers = Offer.objects.filter(restaurant=restaurant)
        context = {"offers": offers}
    
        return render(
            request,
            "./restaurant/offers.html",
            context,
            #   {'form': form}
        )
    except Exception:
        return _handle_view_error(request, "offers")


@login_required(login_url="login")
def offer_create_or_update(request, pk=None):
    try:
        if request.user.user_type != "restaurant":
            messages.error(request, "Not restaurant user")
            return redirect("login")
        if pk:
            offer = get_object_or_404(Offer, pk=pk)
            title = "Update Offer"
        else:
            offer = None
            title = "Add Offer"
    
        restaurant = request.user.restaurantprofile
    
        if request.method == "POST":
            form = OfferForm(request.POST, instance=offer, restaurant=restaurant)
            if form.is_valid():
                new_offer = form.save(commit=False)
                new_offer.restaurant = restaurant  # Force assign correct restaurant
                new_offer.save()
                form.save_m2m()
                return redirect("restaurant-offers")
        else:
            form = OfferForm(instance=offer, restaurant=restaurant)
    
        return render(
            request, "./restaurant/add-offer.html", {"form": form, "title": title}
        )
    except Exception:
        return _handle_view_error(request, "offer_create_or_update")


@login_required(login_url="login")
def offer_delete(request, pk):
    try:
        if request.user.user_type != "restaurant":
            messages.error(request, "Not restaurant user")
            return redirect("login")
        offer = get_object_or_404(Offer, pk=pk)
        offer.delete()
        return redirect("restaurant-offers")
    except Exception:
        return _handle_view_error(request, "offer_delete")


@login_required(login_url="login")
def image_delete(request, pk):
    try:
        if request.user.user_type != "restaurant":
            messages.error(request, "Not restaurant user")
            return redirect("login")
        try:
            image = RestaurantImage.objects.get(pk=pk)
        except RestaurantImage.DoesNotExist:
            messages.error(request, "Image not found or already deleted.")
            return redirect(f'{reverse("restaurant-profile")}?upload=image')
        image.delete()
        messages.success(request, "Image deleted")
        return redirect(f'{reverse("restaurant-profile")}?upload=image')
    except Exception:
        return _handle_view_error(request, "image_delete")


@login_required(login_url="login")
def image_add(request, pk):
    try:
        restaurant = get_object_or_404(RestaurantProfile, id=pk, user=request.user)
        if request.method == "POST" and request.FILES.get("image"):
            image_file = request.FILES["image"]
            if not image_file.content_type.startswith("image/"):
                messages.error(request, "Only image files are allowed.")
                return redirect(f'{reverse("restaurant-profile")}?upload=image')
            if image_file.size > 2 * 1024 * 1024:
                messages.error(request, f"Maximum file size is {2} MB.")
                return redirect(f'{reverse("restaurant-profile")}?upload=image')
            RestaurantImage.objects.create(restaurant=restaurant, image=image_file)
            messages.success(request, "Image added")
        return redirect(f'{reverse("restaurant-profile")}?upload=image')
    except Exception:
        return _handle_view_error(request, "image_add")


@login_required(login_url="login")
def coupons(request):
    try:
        user = request.user
        try:
            restaurant = RestaurantProfile.objects.get(user=user)
        except RestaurantProfile.DoesNotExist:
            return render("restaurant-home")
    
        sort_by = request.GET.get("sort", "delivery_date")  # default: delivery_date
        direction = request.GET.get("dir", "asc")
        order_prefix = "" if direction == "asc" else "-"
        valid_sort_fields = ["delivery_date", "status"]
        sort_field = sort_by if sort_by in valid_sort_fields else "delivery_date"
        coupons = Coupon.objects.filter(restaurant=restaurant).order_by("-created_at")
        user = request.GET.get("user")
        status = request.GET.get("status")
        delivery_date = request.GET.get("delivery_date")
        paginator = Paginator(coupons, 10)  # Show 5 orders per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    
        context = {
            "coupons": page_obj,
            "sort": sort_field,
            "dir": direction,
        }
        return render(request, "./restaurant/coupon.html", context)
    except Exception:
        return _handle_view_error(request, "coupons")


from django.utils import timezone


@login_required(login_url="login")
def payment_dashboard(request):
    try:
        restaurant = request.user.restaurantprofile
    
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        end_of_default = today  # ← Use today as default end date
    
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")
    
        try:
            start_date = (
                datetime.strptime(start_date_str, "%Y-%m-%d").date()
                if start_date_str
                else start_of_month
            )
            end_date = (
                datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if end_date_str
                else end_of_default
            )
        except ValueError:
            start_date, end_date = start_of_month, end_of_default
    
        subscriptions = Subscriptions.objects.filter(
            restaurant=restaurant,
            is_active=True,
            created_at__date__range=(start_date, end_date),
        ).order_by("-created_at")
    
        refunds = Orders.objects.filter(
            restaurant=restaurant,
            status="CANCELLED",
            refund_issued=True,
            delivery_date__range=(start_date, end_date),
        ).order_by("-delivery_date")
    
        total_credits = sum([sub.final_total for sub in subscriptions])
        total_debits = sum(
            [order.food_category.price for order in refunds if order.food_category]
        )
        net_balance = total_credits - total_debits
    
        context = {
            "subscriptions": subscriptions,
            "refunds": refunds,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "net_balance": net_balance,
            "start_date": start_date,
            "end_date": end_date,
        }
    
        return render(request, "restaurant/payment_dashboard.html", context)
    except Exception:
        return _handle_view_error(request, "payment_dashboard")


import csv
from django.http import HttpResponse


@login_required(login_url="login")
def export_payments_csv(request):
    try:
        restaurant = request.user.restaurantprofile
    
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        end_of_default = today
    
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")
    
        try:
            start_date = (
                datetime.strptime(start_date_str, "%Y-%m-%d").date()
                if start_date_str
                else start_of_month
            )
            end_date = (
                datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if end_date_str
                else end_of_default
            )
        except ValueError:
            start_date, end_date = start_of_month, end_of_default
    
        # Get data
        subscriptions = Subscriptions.objects.filter(
            restaurant=restaurant,
            is_active=True,
            created_at__date__range=(start_date, end_date),
        ).order_by("-created_at")
    
        refunds = Orders.objects.filter(
            restaurant=restaurant,
            status="CANCELLED",
            refund_issued=True,
            delivery_date__range=(start_date, end_date),
        ).order_by("-delivery_date")
    
        # Create the response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="payment_report_{timezone.now().strftime("%Y-%m-%d")}.csv"'
        )
    
        writer = csv.writer(response)
    
        # Subscriptions section
        writer.writerow(["=== Subscription Payments ==="])
        writer.writerow(
            [
                "User",
                "Start Date",
                "End Date",
                "Total",
                "Offer Discount",
                "Coupon Discount",
                "Wallet Used",
                "Created At",
            ]
        )
    
        for sub in subscriptions:
            writer.writerow(
                [
                    sub.user.username if sub.user else "Anonymous",
                    sub.start_date.date(),
                    sub.end_date.date(),
                    sub.item_total,
                    sub.offer_discount,
                    sub.discount,
                    sub.wallet_amount_used,
                    sub.created_at.strftime("%Y-%m-%d %H:%M"),
                ]
            )
    
        # Refunds section
        writer.writerow([])
        writer.writerow(["=== Refunds Issued ==="])
        writer.writerow(["User", "Food Category", "Refund Amount", "Delivery Date"])
    
        for refund in refunds:
            writer.writerow(
                [
                    refund.user.username,
                    refund.food_category.name if refund.food_category else "",
                    refund.food_category.price if refund.food_category else "0.00",
                    refund.delivery_date.strftime("%Y-%m-%d"),
                ]
            )
    
        return response
    except Exception:
        return _handle_view_error(request, "export_payments_csv")
