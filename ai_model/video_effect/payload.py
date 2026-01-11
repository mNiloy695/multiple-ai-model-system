def payload_data(model_id,duration=None,effect=None,image=None,resolution=None):
    payload={
    "pixverse/pixverse-v5-effects":{
        "duration": duration,
        "effect":effect,
        "image": image,
        "resolution": resolution
    },
    "kwaivgi/kling-effects":{
        "effect_scene": effect,
        "image": image
    },
    "video-effects/sexy-me":{
        "image":image
    },
    "video-effects/body-shake":{
        "image":image
    }
    }

    if payload[model_id]:
        return payload[model_id]
    return None


