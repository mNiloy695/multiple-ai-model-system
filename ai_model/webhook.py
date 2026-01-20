import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def video_webhook(request):
    if request.method == "POST":
        try:
            event = json.loads(request.body)
            event_type = event.get("type")
            data = event.get("data", {})
            
            if event_type == "video.completed":
                video_id = data.get("id")
                print("Video Completed:", video_id)
                # TODO: Fetch video content using video_id if needed
            elif event_type == "video.failed":
                print("Video Generation Failed:", data)

            return JsonResponse({"status": "received"})
        except Exception as e:
            print("Webhook error:", e)
            return JsonResponse({"status": "error"}, status=400)
    return JsonResponse({"status": "method not allowed"}, status=405)
