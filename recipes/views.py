from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Recipe, Category, Comment, Rating, Feedback, UserProfile, SystemErrorLog, DeveloperInviteCode
from .forms import RecipeForm, CommentForm, RatingForm, RegisterForm, FeedbackForm, DeveloperRegisterForm, UserProfileForm, UserInfoForm, ChangePasswordForm
from django.db.models import Q
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from .models import DeveloperInviteCode
from .forms import DeveloperInviteForm
from django.conf import settings


def home(request):
    categories = Category.objects.all()[:6]
    featured = Recipe.objects.filter(approved=True).order_by('-created_at')[:6]
    return render(request, 'home.html', {'categories': categories, 'featured': featured})


def recipe_list(request):
    qs = Recipe.objects.filter(approved=True).order_by('-created_at')
    categories = Category.objects.all()

    category = request.GET.get('category')
    q = request.GET.get('q')

    if category:
        qs = qs.filter(category__slug=category)

    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(short_description__icontains=q) |
            Q(ingredients__icontains=q)
        )

    return render(request, 'recipes/list.html', {
        'recipes': qs,
        'categories': categories,
        'selected_category': category,
    })


def recipe_detail(request, slug):
    recipe = get_object_or_404(
        Recipe.objects.filter(
            Q(approved=True) | Q(author=request.user)
        ),
        slug=slug
    )

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

        elif 'rate' in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, 'Login required to rate')
                return redirect('login')
            score = int(request.POST.get('score', 5))
            Rating.objects.update_or_create(recipe=recipe, user=request.user, defaults={'score': score})
            messages.success(request, 'Rating saved')
            return redirect('recipe_detail', slug=slug)

        elif 'like' in request.POST or 'dislike' in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, 'Login required')
                return redirect('login')
            if request.user in recipe.likes.all():
                recipe.likes.remove(request.user)
            else:
                recipe.likes.add(request.user)
            return redirect('recipe_detail', slug=slug)

    # Check if current user liked this recipe
    user_liked = request.user.is_authenticated and request.user in recipe.likes.all()

    user_rating = 0
    if request.user.is_authenticated:
        rating_obj = Rating.objects.filter(recipe=recipe, user=request.user).first()
        if rating_obj:
            user_rating = rating_obj.score

    return render(request, 'recipes/detail.html', {
        'recipe': recipe,
        'comment_form': comment_form,
        'user_liked': user_liked,
        'user_rating': user_rating,
    })


@login_required
def recipe_create(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.approved = False
            recipe.save()

            messages.success(request, 'Recipe submitted for review')
            return redirect('recipe_list')

    else:
        form = RecipeForm()

    return render(request, 'recipes/form.html', {'form': form, 'title': 'Add Recipe'})


@login_required
def recipe_edit(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug, author=request.user)
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recipe updated')
            return redirect('recipe_detail', slug=recipe.slug)
    else:
        form = RecipeForm(instance=recipe)
    return render(request, 'recipes/form.html', {'form': form, 'title': 'Edit Recipe'})


@login_required
def recipe_delete(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug)
    if request.user != recipe.author and not request.user.is_staff:
        return HttpResponseForbidden()

    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Recipe deleted')
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('recipe_list')
    return render(request, 'recipes/confirm_delete.html', {'object': recipe})


@login_required
def recipe_approve(request, slug):
    if not request.user.is_staff:
        return HttpResponseForbidden()

    recipe = get_object_or_404(Recipe, slug=slug)
    recipe.approved = True
    recipe.save()

    messages.success(request, 'Recipe approved successfully!')
    return redirect('admin_dashboard')


@login_required
def recipe_preview(request, slug):
    if not request.user.is_staff:
        return HttpResponseForbidden()

    recipe = get_object_or_404(Recipe, slug=slug)
    comment_form = CommentForm()

    return render(request, 'recipes/detail.html', {
        'recipe': recipe,
        'comment_form': comment_form
    })


def search(request):
    if request.method == 'POST':
        q = request.POST.get('q', '')
        return redirect(f'/recipes/?q={q}')
    return recipe_list(request)


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please login.', extra_tags='success')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'auth/register.html', {'form': form})


def register_dev_view(request):
    if request.method == 'POST':
        form = DeveloperRegisterForm(request.POST)
        if form.is_valid():
            code_str = form.cleaned_data['invite_code']
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            
            invite = DeveloperInviteCode.objects.get(code=code_str)
            invite.is_active = False
            invite.used_by = user
            invite.save()

            messages.success(request, 'Developer account created. You have full access.', extra_tags='success')
            return redirect('login')
    else:
        form = DeveloperRegisterForm()
    return render(request, 'dev/register.html', {'form': form})


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


@user_passes_test(staff_check)
def error_dashboard(request):
    """Developer only dashboard for monitoring errors."""
    errors = SystemErrorLog.objects.all().order_by('-created_at')
    show_resolved = request.GET.get('resolved') == 'true'
    if not show_resolved:
        errors = errors.filter(resolved=False)
    return render(request, 'dev/error_dashboard.html', {'errors': errors, 'showing_resolved': show_resolved})


@user_passes_test(staff_check)
@require_POST
def resolve_error(request, error_id):
    error = get_object_or_404(SystemErrorLog, id=error_id)
    error.delete()
    messages.success(request, 'Error log resolved and deleted.')
    return redirect('error_dashboard')


# ==========================================
# CUSTOM HANDLERS
# ==========================================

def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
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


def developer_invite_add(request):
    form = DeveloperInviteForm()

    if request.method == "POST":
        form = DeveloperInviteForm(request.POST)

        if form.is_valid():
            code = form.cleaned_data["code"]
            key = form.cleaned_data["verify_key"]

            # 🔐 security check
            if key != settings.DEVELOPER_MASTER_KEY:
                messages.error(request, "❌ Wrong security key")
                return redirect("dev_invite_add")

            DeveloperInviteCode.objects.create(code=code)

            messages.success(request, "✅ Invite code added successfully")
            return redirect("dev_invite_add")

    return render(request, "dev/add_invite.html", {"form": form})