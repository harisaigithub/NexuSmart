# views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import logging
from .models import Chat


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your Gemini API key
GEMINI_API_KEY = 'API_KEY'
GEMINI_API_URL = 'https://api.gemini.com/v1/chat'

@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        try:
            question = request.POST.get('question')
            if not question:
                return JsonResponse({'error': 'No question provided'}, status=400)
            
            logger.info(f"Received question: {question}")

            # Make a request to the Gemini API
            response = requests.post(
                GEMINI_API_URL,
                headers={'Authorization': f'Bearer {GEMINI_API_KEY}'},
                json={'question': question}
            )

            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.text}")
                return JsonResponse({'error': 'Failed to get response from Gemini API'}, status=response.status_code)

            response_data = response.json()
            logger.info(f"Response: {response_data}")

            answer = response_data.get('answer')
            if not answer:
                logger.error("No answer found in the Gemini API response")
                return JsonResponse({'error': 'No answer found'}, status=500)

            Chat.objects.create(question=question, answer=answer)
            return JsonResponse({'answer': answer})
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
    else:
        return render(request, 'chatbot.html')