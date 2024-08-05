from django.shortcuts import render,redirect
from django.views.generic import ListView,DetailView,CreateView,UpdateView,DeleteView,FormView
from django.http import HttpRequest, HttpResponse
from pantry.models import Collection,Item
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy,reverse
import json,re
# Create your views here.

from groq import Groq

client = Groq(api_key='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')


class CollectionList(LoginRequiredMixin,ListView):
    model = Collection
    context_object_name = "collections"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['collections']=context['collections'].filter(user=self.request.user)
        search_input = self.request.GET.get('search-area') or ''
        if search_input:
            context['collections']=context['collections'].filter(name__icontains=search_input)
        context['search_input'] = search_input
        return context

class CollectionCreate(LoginRequiredMixin,CreateView):
    model = Collection
    fields = ['name']
    success_url = reverse_lazy('collections')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(CollectionCreate,self).form_valid(form)

class ItemCreate(LoginRequiredMixin,CreateView):
    model = Item
    fields = ['name','image']
    # success_url = reverse_lazy('items',)
    def get_success_url(self):
        # Extract the collection_id from the form's instance
        collection_id = self.object.collection_id
        return reverse('items', kwargs={'collection_id': collection_id})

    def form_valid(self, form):
        form.instance.user = self.request.user
        # Set the collection field from URL parameters
        collection_id = self.kwargs.get('collection_id')
        form.instance.collection = Collection.objects.get(id=collection_id)
        print("Collection ID: ",collection_id)
        print(form.errors)
        return super(ItemCreate, self).form_valid(form)
    

class CollectionUpdate(LoginRequiredMixin,UpdateView):
    model = Collection
    fields = ['id','name']
    success_url = reverse_lazy('collections')

class ItemUpdate(LoginRequiredMixin,UpdateView):
    model = Item
    fields = ['name','image']
    
    def get_success_url(self):
        # Extract the collection_id from the form's instance
        collection_id = self.object.collection_id
        return reverse('items', kwargs={'collection_id': collection_id})
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['collection_id'] = self.object.collection_id
        return context

class CollectionDelete(LoginRequiredMixin,DeleteView):
    model = Collection
    context_object_name = 'collection'
    success_url = reverse_lazy('collections')

class ItemDelete(LoginRequiredMixin,DeleteView):
    model = Item
    context_object_name = 'item'
    def get_success_url(self):
        # Extract the collection_id from the form's instance
        collection_id = self.object.collection_id
        return reverse('items', kwargs={'collection_id': collection_id})
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['collection_id'] = self.object.collection_id
        return context

class CustomLoginView(LoginView):
    template_name = 'pantry/login.html'
    fields = '__all__'
    redirect_authenticated_user = True
    def get_success_url(self):
        return reverse_lazy('collections')
    
class RegisterPage(FormView):
    template_name = 'pantry/register.html'
    form_class = UserCreationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy("login")
    print("I am accessed")
    def form_valid(self, form):
        user = form.save()
        if user is not None:
            login(self.request, user)
        return super(RegisterPage, self).form_valid(form)

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('collections')
        return super(RegisterPage,self).get(*args, **kwargs)
    
def ItemList(request,collection_id):
    context = {'collection_id':collection_id}
    ingredients_list = []
    if request.user.is_authenticated:
        print("Test: Collection_id = ",collection_id)
        items = Item.objects.filter(collection=collection_id)
        print(items)
        context['items'] = items
        search_input = request.GET.get('search-area') or ''
        if search_input:
            context['items']=context['items'].filter(name__icontains=search_input)
        context['search_input'] = search_input
        for i in items:
            ingredients_list.append(i.name)
        # print(ingredients_list)
        context['serialized_list']=json.dumps(ingredients_list)
        return render(request,'pantry/item_list.html',context)

    else:
        reverse_lazy('login')

def extract_recipe_parts(response):
    # Use regex to extract the parts
    title_pattern1 = r'Title:\s*(.+)'
    title_pattern2 = r'^\s*(.*?)\s*\n\s*Ingredients:'
    ingredients_pattern = r'Ingredients:\s*((?:.|\s)+?)\n\s*Process:'
    process_pattern = r'Process:\s*((?:.|\s)+)$'

    # Perform regex search
    title_match1 = re.search(title_pattern1, response)
    title_match2 = re.search(title_pattern2, response, re.MULTILINE)
    ingredients_match = re.search(ingredients_pattern, response, re.MULTILINE)
    process_match = re.search(process_pattern, response, re.MULTILINE)

    # Extract the matched groups or default to empty strings if not found
    if title_match1:
        title = title_match1.group(1).strip()
    elif title_match2:
        title = title_match2.group(1).strip()
    else:
        title = ''

    ingredients = ingredients_match.group(1).strip() if ingredients_match else ''
    process = process_match.group(1).strip() if process_match else ''

    return {
        'title': title,
        'ingredients': ingredients,
        'process': process
    }


def asklama(ingredients):
    prompt = '''I have the following ingredients: {}. Generate a recipe using these ingredients with the following format:

        Title: [Creative title here]
        Ingredients:
        - [First ingredient]
        - [Second ingredient]
        - [Third ingredient]

        Process:
        1. [First step]
        2. [Second step]
        3. [Third step]

        Ensure the response follows this format exactly and is in plain text with no markdown language symbols.
        '''.format(ingredients)

    response = client.chat.completions.create(
        messages = [
            {
                'role':'user',
                'content':prompt
            }
        ],
        model = 'llama-3.1-8b-instant'
    )
    response = response.to_dict()
    response = response['choices'][0]['message']['content']
    print(response)
    return extract_recipe_parts(response)

def getRecipe(request):
    context = {}
    if request.user.is_authenticated:
        serialized_list = request.GET.get('my_list', '[]')
        # print(serialized_list)
        ing_list = json.loads(serialized_list)
        # print(ing_list)
        ingredients = ", ".join(ing_list)
        print(ingredients)
        response = asklama(ingredients)
        context['title'] = response['title']
        print(context['title'])
        context['ingredients'] = response['ingredients']
        context['process'] = response['process']

        return render(request,'pantry/recipe.html',context)
    else:
        reverse_lazy('login')
    



    