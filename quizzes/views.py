"""Demo-only practice tests & quizzes. No DB models: sample data scored in-browser via vidya.js."""
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


SAMPLE_TESTS = [
    {'slug': 'python-basics', 'title': 'Python Basics', 'questions': 10, 'duration': 600, 'difficulty': 'Beginner', 'category': 'Programming', 'desc': 'Variables, loops, functions and OOP fundamentals.'},
    {'slug': 'django-web', 'title': 'Django Web Development', 'questions': 12, 'duration': 900, 'difficulty': 'Intermediate', 'category': 'Web', 'desc': 'Models, views, templates, auth and DRF basics.'},
    {'slug': 'js-frontend', 'title': 'JavaScript Frontend', 'questions': 10, 'duration': 600, 'difficulty': 'Beginner', 'category': 'Web', 'desc': 'DOM, events, fetch and ES6+ essentials.'},
    {'slug': 'data-sql', 'title': 'SQL & Data Skills', 'questions': 15, 'duration': 1200, 'difficulty': 'Advanced', 'category': 'Data', 'desc': 'Joins, aggregation, indexes and query design.'},
]

SAMPLE_QUIZZES = {
    'python-basics': [
        {'q': 'Which keyword defines a function in Python?', 'options': ['func', 'def', 'function', 'lambda-def'], 'answer': 1},
        {'q': 'What is the output of len([1, 2, 3])?', 'options': ['2', '3', '6', 'Error'], 'answer': 1},
        {'q': 'Which data type is mutable?', 'options': ['tuple', 'str', 'list', 'int'], 'answer': 2},
        {'q': 'How do you start a for loop over range(5)?', 'options': ['for i in range(5):', 'foreach i in 5', 'loop 5 times', 'for(i=0;i<5)'], 'answer': 0},
        {'q': 'What does pip do?', 'options': ['Runs Python', 'Installs packages', 'Formats code', 'Creates venv only'], 'answer': 1},
    ],
    'django-web': [
        {'q': 'Which file defines URL routes in Django?', 'options': ['views.py', 'urls.py', 'models.py', 'settings.py'], 'answer': 1},
        {'q': 'What does get_or_create do?', 'options': ['Always creates', 'Fetches or creates atomically', 'Deletes', 'Migrates'], 'answer': 1},
        {'q': 'Which mixin requires login?', 'options': ['LoginRequiredMixin', 'AuthMixin', 'UserPasses', 'SessionMixin'], 'answer': 0},
        {'q': 'Default Django template folder setting?', 'options': ['TEMPLATES DIRS', 'STATIC_ROOT', 'MEDIA_URL', 'APPS'], 'answer': 0},
        {'q': 'DRF stands for?', 'options': ['Django Rest Framework', 'Direct Render Forms', 'Data Relay Format', 'Dynamic Rest Files'], 'answer': 0},
    ],
    'js-frontend': [
        {'q': 'Which keyword declares a block-scoped variable?', 'options': ['var', 'let', 'def', 'dim'], 'answer': 1},
        {'q': 'JSON.parse does what?', 'options': ['Stringifies', 'Parses a JSON string', 'Fetches data', 'Validates HTML'], 'answer': 1},
        {'q': 'Which method selects all matching elements?', 'options': ['querySelector', 'querySelectorAll', 'getElement', 'findAll'], 'answer': 1},
        {'q': 'fetch returns a...', 'options': ['String', 'Promise', 'Array', 'Number'], 'answer': 1},
        {'q': 'localStorage stores...', 'options': ['Server sessions', 'Browser key-value strings', 'Cookies only', 'SQL rows'], 'answer': 1},
    ],
    'data-sql': [
        {'q': 'Which clause filters aggregated rows?', 'options': ['WHERE', 'HAVING', 'ORDER BY', 'LIMIT'], 'answer': 1},
        {'q': 'INNER JOIN returns...', 'options': ['All rows both sides', 'Only matching rows', 'Only left rows', 'Cross product'], 'answer': 1},
        {'q': 'Primary key must be...', 'options': ['Nullable', 'Unique + not null', 'Indexed text only', 'Foreign'], 'answer': 1},
        {'q': 'Which improves lookup speed?', 'options': ['Index', 'View', 'Trigger', 'Comment'], 'answer': 0},
        {'q': 'COUNT(*) counts...', 'options': ['Null columns', 'Rows', 'Tables', 'Distinct only'], 'answer': 1},
    ],
}


class TestListView(LoginRequiredMixin, TemplateView):
    template_name = 'quizzes/test_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tests'] = SAMPLE_TESTS
        return ctx


class QuizTakeView(LoginRequiredMixin, TemplateView):
    template_name = 'quizzes/quiz_take.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug', 'python-basics')
        test = next((t for t in SAMPLE_TESTS if t['slug'] == slug), SAMPLE_TESTS[0])
        questions = SAMPLE_QUIZZES.get(slug, SAMPLE_QUIZZES['python-basics'])
        ctx['test'] = test
        ctx['quiz_json'] = json.dumps(questions)
        return ctx
