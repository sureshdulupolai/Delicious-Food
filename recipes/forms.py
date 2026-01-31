from django import forms
from .models import Recipe, Comment, Rating, Feedback, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.text import slugify


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'category', 'image', 'short_description', 'ingredients', 'steps']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipe name'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows':2, 'placeholder': 'Brief description...'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows':6, 'placeholder': 'One ingredient per line'}),
            'steps': forms.Textarea(attrs={'class': 'form-control', 'rows':8, 'placeholder': 'Number your steps: 1. ... 2. ...'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows':3, 'placeholder':'Share your thoughts...'}),
        }


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score']


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows':4}),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control password-field'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control password-field'})

    def _suggest_usernames(self, base, max_suggestions=3):
        """Generate available username suggestions based on `base`."""
        suggestions = []
        candidate = base
        suffix = 1
        # normalize base
        base_slug = slugify(base).replace('-', '') or base
        while len(suggestions) < max_suggestions:
            if suffix == 1:
                candidate = base_slug
            else:
                candidate = f"{base_slug}{suffix}"
            if not User.objects.filter(username__iexact=candidate).exists():
                suggestions.append(candidate)
            suffix += 1
        return suggestions

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username__iexact=username).exists():
            suggestions = self._suggest_usernames(username)
            raise forms.ValidationError(
                f"Username '{username}' is already taken. Suggestions: {', '.join(suggestions)}"
            )
        return username


class DeveloperRegisterForm(RegisterForm):
    invite_code = forms.CharField(
        label='Invite code', 
        widget=forms.PasswordInput(attrs={'class': 'form-control invite-code-field', 'placeholder': 'Invite code'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control password-field'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control password-field'})

    def clean_invite_code(self):
        code = self.cleaned_data.get('invite_code')
        from django.conf import settings
        if not getattr(settings, 'DEVELOPER_INVITE_CODE', None) or code != settings.DEVELOPER_INVITE_CODE:
            raise forms.ValidationError('Invalid invite code.')
        return code


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'bio']
        widgets = {
            'profile_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tell us about yourself...'}),
        }


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
        }

    def _suggest_usernames(self, base, max_suggestions=3):
        suggestions = []
        candidate = base
        suffix = 1
        base_slug = slugify(base).replace('-', '') or base
        while len(suggestions) < max_suggestions:
            if suffix == 1:
                candidate = base_slug
            else:
                candidate = f"{base_slug}{suffix}"
            # exclude current instance from check
            if not User.objects.filter(username__iexact=candidate).exclude(pk=self.instance.pk).exists():
                suggestions.append(candidate)
            suffix += 1
        return suggestions

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if another user has this username
            qs = User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
            if qs.exists():
                suggestions = self._suggest_usernames(username)
                raise forms.ValidationError(
                    f"Username '{username}' is already taken. Suggestions: {', '.join(suggestions)}"
                )
        return username


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control current-password-field', 'placeholder': 'Enter current password'})
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control new-password-field', 'placeholder': 'Enter new password'})
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control new-password-field', 'placeholder': 'Confirm new password'})
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError('Current password is incorrect.')
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError('New passwords do not match.')
        
        return cleaned_data