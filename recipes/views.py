from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Recipe, Category, Comment, Rating, Feedback, UserProfile
from .forms import RecipeForm, CommentForm, RatingForm, RegisterForm, FeedbackForm, DeveloperRegisterForm, UserProfileForm, UserInfoForm, ChangePasswordForm
from django.db.models import Q
from django.contrib.auth.models import User


def home(request):
    categories = Category.objects.all()[:6]
    featured = Recipe.objects.filter(approved=True).order_by('-created_at')[:6]
    return render(request, 'home.html', {'categories': categories, 'featured': featured})


def recipe_list(request):
    qs = Recipe.objects.filter(approved=True).order_by('-created_at')
    category = request.GET.get('category')
    q = request.GET.get('q')
    if category:
        qs = qs.filter(category__slug=category)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(short_description__icontains=q) | Q(ingredients__icontains=q))
    return render(request, 'recipes/list.html', {'recipes': qs})


def recipe_detail(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug, approved=True)
    comment_form = CommentForm()
    if request.method == 'POST':
        if 'comment' in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, 'Login required to comment')
                return redirect('login')
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.user = request.user
                comment.recipe = recipe
                comment.save()
                messages.success(request, 'Comment added')
                return redirect('recipe_detail', slug=slug)
        if 'rate' in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, 'Login required to rate')
                return redirect('login')
            score = int(request.POST.get('score', 5))
            Rating.objects.update_or_create(recipe=recipe, user=request.user, defaults={'score': score})
            messages.success(request, 'Rating saved')
            return redirect('recipe_detail', slug=slug)
        if 'like' in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, 'Login required to like')
                return redirect('login')
            if request.user in recipe.likes.all():
                recipe.likes.remove(request.user)
            else:
                recipe.likes.add(request.user)
            return redirect('recipe_detail', slug=slug)

    return render(request, 'recipes/detail.html', {'recipe': recipe, 'comment_form': comment_form})


@login_required
def recipe_create(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            # mark pending approval
            recipe.approved = False
            recipe.save()
            messages.success(request, 'Recipe submitted for review')
            return redirect('recipe_detail', slug=recipe.slug)
    else:
        form = RecipeForm()
    return render(request, 'recipes/form.html', {'form': form, 'title': 'Add Recipe'})


@login_required
def recipe_edit(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug, author=request.user)
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recipe updated')
            return redirect('recipe_detail', slug=recipe.slug)
    else:
        form = RecipeForm(instance=recipe)
    return render(request, 'recipes/form.html', {'form': form, 'title': 'Edit Recipe'})


@login_required
def recipe_delete(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug, author=request.user)
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Recipe deleted')
        return redirect('recipe_list')
    return render(request, 'recipes/confirm_delete.html', {'object': recipe})


def search(request):
    return recipe_list(request)


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please login with your credentials.', extra_tags='success')
            return redirect('login')
        else:
            # Don't show top-level error message, let form handle it
            pass
    else:
        form = RegisterForm()
    return render(request, 'auth/register.html', {'form': form})


def register_dev_view(request):
    """Protected developer registration that creates a superuser/staff account when a valid invite code is provided.

    The view uses `DeveloperRegisterForm` which validates `invite_code` against
    `settings.DEVELOPER_INVITE_CODE`. On success the user is created with
    `is_staff=True` and `is_superuser=True` and redirected to login.
    """
    if request.method == 'POST':
        form = DeveloperRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            messages.success(request, 'Developer account created. You can now login.', extra_tags='success')
            return redirect('login')
        else:
            pass
    else:
        form = DeveloperRegisterForm()
    return render(request, 'auth/register_dev.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Logged in successfully!', extra_tags='success')
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials. Please try again.', extra_tags='error')
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!', extra_tags='success')
    return redirect('home')


def staff_check(user):
    return user.is_staff


@user_passes_test(staff_check)
def admin_dashboard(request):
    users = User.objects.all()
    pending = Recipe.objects.filter(approved=False).order_by('-created_at')
    feedbacks = Feedback.objects.all().order_by('-created_at')
    return render(request, 'admin/dashboard.html', {'users': users, 'pending': pending, 'feedbacks': feedbacks})


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


@login_required
def profile_view(request):
    """User profile page with image upload and two forms for info and password change"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    # initialize forms so they exist for both GET and POST paths
    profile_form = UserProfileForm(instance=user_profile)
    info_form = UserInfoForm(instance=request.user)
    password_form = ChangePasswordForm(request.user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!', extra_tags='success')
                return redirect('profile')
        
        elif 'update_info' in request.POST:
            info_form = UserInfoForm(request.POST, instance=request.user)
            if info_form.is_valid():
                info_form.save()
                messages.success(request, 'Account information updated successfully!', extra_tags='success')
                return redirect('profile')
        
        elif 'change_password' in request.POST:
            password_form = ChangePasswordForm(request.user, request.POST)
            if password_form.is_valid():
                new_password = password_form.cleaned_data.get('new_password1')
                request.user.set_password(new_password)
                request.user.save()
                login(request, request.user)
                messages.success(request, 'Password changed successfully!', extra_tags='success')
                return redirect('profile')
    
    
    return render(request, 'auth/profile.html', {
        'profile_form': profile_form,
        'info_form': info_form,
        'password_form': password_form,
        'user_profile': user_profile
    })
