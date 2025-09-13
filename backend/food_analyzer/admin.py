from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import FoodAnalysis, UserFeedback, FoodDatabase, SystemStatistics, LearningCache


# Custom filter to replace nonexistent admin.RangeFilter
class ConfidenceRangeFilter(admin.SimpleListFilter):
    title = 'confidence'
    parameter_name = 'confidence_range'

    def lookups(self, request, model_admin):
        return (
            ('high', 'High (>=80%)'),
            ('medium', 'Medium (60-79%)'),
            ('low', 'Low (<60%)'),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == 'high':
            return queryset.filter(confidence__gte=80)
        if val == 'medium':
            return queryset.filter(confidence__gte=60, confidence__lt=80)
        if val == 'low':
            return queryset.filter(confidence__lt=60)
        return queryset


@admin.register(FoodAnalysis)
class FoodAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'food_name', 'confidence', 'confidence_level', 'calories_kcal', 
        'data_source', 'created_at', 'processing_time', 'feedback_count'
    ]
    list_filter = [
        'data_source', 'model_used', 'created_at',
    ConfidenceRangeFilter,
    ]
    search_fields = ['food_name', 'data_source']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'processing_time', 
        'image_preview', 'nutrition_summary', 'feedback_summary'
    ]
    fieldsets = [
        ('Detection Results', {
            'fields': ('food_name', 'confidence', 'confidence_level', 'image', 'image_preview')
        }),
        ('Nutrition Information', {
            'fields': ('calories_kcal', 'protein_g', 'fat_g', 'carbs_g', 'fiber_g', 'sugar_g', 'sodium_mg', 'serving_size'),
            'classes': ['collapse']
        }),
        ('Analysis Metadata', {
            'fields': ('model_used', 'data_source', 'processing_time'),
            'classes': ['collapse']
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ['collapse']
        }),
        ('Summary', {
            'fields': ('nutrition_summary', 'feedback_summary'),
            'classes': ['collapse']
        })
    ]
    
    def confidence_level(self, obj):
        if obj.confidence >= 80:
            color = 'green'
            level = 'High'
        elif obj.confidence >= 60:
            color = 'orange'
            level = 'Medium'
        else:
            color = 'red'
            level = 'Low'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({:.1f}%)</span>',
            color, level, obj.confidence
        )
    confidence_level.short_description = 'Confidence Level'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.image.url
            )
        return 'No image'
    image_preview.short_description = 'Image Preview'
    
    def nutrition_summary(self, obj):
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>Per 100g:</strong><br>'
            '🔥 Calories: {:.0f} kcal<br>'
            '🥩 Protein: {:.1f}g<br>'
            '🥑 Fat: {:.1f}g<br>'
            '🌾 Carbs: {:.1f}g<br>'
            '🥬 Fiber: {:.1f}g<br>'
            '🍯 Sugar: {:.1f}g<br>'
            '🧂 Sodium: {:.0f}mg'
            '</div>',
            obj.calories_kcal or 0, obj.protein_g or 0, obj.fat_g or 0,
            obj.carbs_g or 0, obj.fiber_g or 0, obj.sugar_g or 0, obj.sodium_mg or 0
        )
    nutrition_summary.short_description = 'Nutrition Summary'
    
    def feedback_count(self, obj):
        count = obj.feedbacks.count()
        if count > 0:
            return format_html(
                '<a href="{}?food_analysis__id={}">{} feedback(s)</a>',
                reverse('admin:food_analyzer_userfeedback_changelist'),
                obj.id, count
            )
        return '0 feedbacks'
    feedback_count.short_description = 'User Feedback'
    
    def feedback_summary(self, obj):
        feedbacks = obj.feedbacks.all()
        if not feedbacks:
            return 'No feedback received'
        
        summary = '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
        summary += '<strong>Feedback Summary:</strong><br>'
        
        for feedback in feedbacks[:5]:  # Show last 5 feedbacks
            color = 'green' if feedback.feedback_type in ['perfect', 'confirmation'] else 'orange'
            summary += f'<span style="color: {color};">• {feedback.get_feedback_type_display()}</span><br>'
        
        if feedbacks.count() > 5:
            summary += f'... and {feedbacks.count() - 5} more'
        
        summary += '</div>'
        return format_html(summary)
    feedback_summary.short_description = 'Feedback Summary'


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'predicted_food', 'correct_food', 'feedback_type', 'original_confidence',
        'correction_reason', 'created_at', 'analysis_link'
    ]
    list_filter = ['feedback_type', 'correction_reason', 'created_at']
    search_fields = ['predicted_food', 'correct_food', 'user_notes']
    readonly_fields = ['created_at', 'analysis_details']
    
    fieldsets = [
        ('Feedback Information', {
            'fields': ('feedback_type', 'predicted_food', 'correct_food', 'original_confidence')
        }),
        ('Additional Details', {
            'fields': ('correction_reason', 'user_notes', 'user')
        }),
        ('System Information', {
            'fields': ('food_analysis', 'created_at', 'analysis_details'),
            'classes': ['collapse']
        })
    ]
    
    def analysis_link(self, obj):
        if obj.food_analysis:
            return format_html(
                '<a href="{}">View Analysis</a>',
                reverse('admin:food_analyzer_foodanalysis_change', args=[obj.food_analysis.id])
            )
        return 'No analysis'
    analysis_link.short_description = 'Related Analysis'
    
    def analysis_details(self, obj):
        if obj.food_analysis:
            analysis = obj.food_analysis
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                '<strong>Analysis Details:</strong><br>'
                'Food: {}<br>'
                'Confidence: {:.1f}%<br>'
                'Model: {}<br>'
                'Created: {}'
                '</div>',
                analysis.food_name, analysis.confidence,
                analysis.model_used, analysis.created_at.strftime('%Y-%m-%d %H:%M')
            )
        return 'No analysis available'
    analysis_details.short_description = 'Analysis Details'


@admin.register(FoodDatabase)
class FoodDatabaseAdmin(admin.ModelAdmin):
    list_display = [
        'food_name', 'category', 'calories_kcal', 'data_source',
        'data_quality', 'search_count', 'last_searched'
    ]
    list_filter = ['category', 'data_source', 'data_quality']
    search_fields = ['food_name', 'alternative_names']
    readonly_fields = ['search_count', 'last_searched', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Food Information', {
            'fields': ('food_name', 'alternative_names', 'category')
        }),
        ('Nutrition Data', {
            'fields': (
                'calories_kcal', 'protein_g', 'fat_g', 'carbs_g',
                'fiber_g', 'sugar_g', 'sodium_mg'
            ),
            'classes': ['collapse']
        }),
        ('Additional Nutrients', {
            'fields': ('calcium_mg', 'iron_mg', 'vitamin_c_mg', 'vitamin_a_ug'),
            'classes': ['collapse']
        }),
        ('Data Source', {
            'fields': ('data_source', 'source_url', 'data_quality')
        }),
        ('Usage Statistics', {
            'fields': ('search_count', 'last_searched'),
            'classes': ['collapse']
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        })
    ]


@admin.register(SystemStatistics)
class SystemStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_predictions', 'accuracy_rate', 'high_confidence_accuracy',
        'total_corrections', 'nutrition_success_rate', 'last_updated'
    ]
    list_filter = ['date']
    readonly_fields = [
        'date', 'last_updated', 'performance_summary', 'confidence_breakdown',
        'learning_summary'
    ]
    
    fieldsets = [
        ('Performance Metrics', {
            'fields': (
                'total_predictions', 'correct_predictions', 'accuracy_rate',
                'average_processing_time'
            )
        }),
        ('Confidence-Based Metrics', {
            'fields': (
                'high_confidence_predictions', 'high_confidence_correct',
                'medium_confidence_predictions', 'medium_confidence_correct',
                'low_confidence_predictions', 'low_confidence_correct'
            ),
            'classes': ['collapse']
        }),
        ('Learning Metrics', {
            'fields': ('total_corrections', 'total_confirmations')
        }),
        ('Nutrition API Metrics', {
            'fields': ('total_nutrition_searches', 'successful_nutrition_searches'),
            'classes': ['collapse']
        }),
        ('System Information', {
            'fields': ('date', 'last_updated'),
            'classes': ['collapse']
        }),
        ('Summary Views', {
            'fields': ('performance_summary', 'confidence_breakdown', 'learning_summary'),
            'classes': ['collapse']
        })
    ]
    
    def nutrition_success_rate(self, obj):
        return f"{obj.nutrition_search_success_rate:.1f}%"
    nutrition_success_rate.short_description = 'Nutrition Success Rate'
    
    def performance_summary(self, obj):
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>Performance Summary for {}:</strong><br><br>'
            '📊 Overall Accuracy: {:.1f}%<br>'
            '🎯 Total Predictions: {}<br>'
            '✅ Correct Predictions: {}<br>'
            '⚡ Avg Processing Time: {:.2f}s<br>'
            '🌐 Nutrition Success: {:.1f}%'
            '</div>',
            obj.date, obj.accuracy_rate, obj.total_predictions,
            obj.correct_predictions, obj.average_processing_time,
            obj.nutrition_search_success_rate
        )
    performance_summary.short_description = 'Performance Summary'
    
    def confidence_breakdown(self, obj):
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>Confidence-Based Performance:</strong><br><br>'
            '🟢 High Confidence (≥80%): {}/{} ({:.1f}%)<br>'
            '🟡 Medium Confidence (60-79%): {}/{} ({:.1f}%)<br>'
            '🔴 Low Confidence (<60%): {}/{} ({:.1f}%)'
            '</div>',
            obj.high_confidence_correct, obj.high_confidence_predictions, obj.high_confidence_accuracy,
            obj.medium_confidence_correct, obj.medium_confidence_predictions, obj.medium_confidence_accuracy,
            obj.low_confidence_correct, obj.low_confidence_predictions, obj.low_confidence_accuracy
        )
    confidence_breakdown.short_description = 'Confidence Breakdown'
    
    def learning_summary(self, obj):
        total_feedback = obj.total_corrections + obj.total_confirmations
        if total_feedback > 0:
            confirmation_rate = (obj.total_confirmations / total_feedback) * 100
        else:
            confirmation_rate = 0.0
            
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>Learning System Performance:</strong><br><br>'
            '📚 Total Corrections: {}<br>'
            '✅ Total Confirmations: {}<br>'
            '🎯 Confirmation Rate: {:.1f}%<br>'
            '📈 Learning Progress: {}'
            '</div>',
            obj.total_corrections, obj.total_confirmations, confirmation_rate,
            'Improving' if confirmation_rate > 70 else 'Needs Attention' if confirmation_rate < 50 else 'Good'
        )
    learning_summary.short_description = 'Learning Summary'


@admin.register(LearningCache)
class LearningCacheAdmin(admin.ModelAdmin):
    list_display = [
        'predicted_food', 'correct_food', 'occurrence_count',
        'confidence_boost', 'success_rate', 'last_seen'
    ]
    list_filter = ['first_seen', 'last_seen']
    search_fields = ['predicted_food', 'correct_food']
    readonly_fields = ['first_seen', 'last_seen', 'pattern_strength']
    
    fieldsets = [
        ('Learning Pattern', {
            'fields': ('predicted_food', 'correct_food')
        }),
        ('Pattern Statistics', {
            'fields': (
                'occurrence_count', 'confidence_boost', 'success_rate',
                'average_original_confidence'
            )
        }),
        ('Timestamps', {
            'fields': ('first_seen', 'last_seen'),
            'classes': ['collapse']
        }),
        ('Pattern Analysis', {
            'fields': ('pattern_strength',),
            'classes': ['collapse']
        })
    ]
    
    def pattern_strength(self, obj):
        strength = 'Weak'
        color = 'red'
        
        if obj.occurrence_count >= 10:
            strength = 'Very Strong'
            color = 'green'
        elif obj.occurrence_count >= 5:
            strength = 'Strong'
            color = 'blue'
        elif obj.occurrence_count >= 3:
            strength = 'Moderate'
            color = 'orange'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span><br>'
            '<small>Used {} times with {:.1f}% success rate</small>',
            color, strength, obj.occurrence_count, obj.success_rate
        )
    pattern_strength.short_description = 'Pattern Strength'


# Custom admin site configuration
admin.site.site_header = "Enhanced Food Detection Admin"
admin.site.site_title = "Food Detection Admin"
admin.site.index_title = "Welcome to Food Detection Administration"