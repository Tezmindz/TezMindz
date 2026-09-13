def gamification_context(request):
    """
    Injects real XP and Credit account data into all templates for authenticated students.
    """
    context = {
        'global_xp': 0,
        'global_level': 1,
        'global_coins': 0,
        'global_streak': 0,
        'global_rank': 'Novice'
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        from apps.gamification.models import XPAccount, CreditAccount, XPLevelThreshold
        
        student = request.user.student_profile
        
        # XP
        xp_account = XPAccount.objects.filter(student=student).first()
        if xp_account:
            context['global_xp'] = xp_account.total_xp
            context['global_level'] = xp_account.current_level
            
            # Simple rank mapping based on level (custom logic can replace this)
            if xp_account.current_level >= 10:
                context['global_rank'] = 'Master'
            elif xp_account.current_level >= 5:
                context['global_rank'] = 'Explorer'
                
        # Coins
        credit_account = CreditAccount.objects.filter(student=student).first()
        if credit_account:
            context['global_coins'] = credit_account.balance
            
        # Streak (mocked for now, assuming it's from another model or StudentProfile)
        context['global_streak'] = getattr(student, 'current_streak', 0)
        
    return context
