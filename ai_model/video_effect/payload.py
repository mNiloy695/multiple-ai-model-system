def payload_data(model_id,duration=None,effect=None,image=None,resolution=None,bgm=False,template="sexy_devil",seed=0,sound_effect_switch=False):

    print("model is is ",model_id)


    if model_id=="pixverse/pixverse-v5-effects":
        resolution_allowed=["540p","360p","720p","1080p"]
        if resolution not in resolution_allowed:
            resolution="540p"


    if model_id=="vidu/template/halloween":
        template_list = ["tim_burton","broomstick_fly","witchy_pet","pumpkin_head","sexy_devil","dance_with_ghost","crow_arrival","clown_makeup","shadow_of_terror_video","not_look_back_video","turn_into_zombie","head_to_balloon","covered_liquid_metal","wednesdays_vibe"]
        if template not in template_list:
             template="sexy_devil"


    if model_id=="video-effects/dust-me-away" or model_id=="video-effects/red-or-white":
        resolution_allowed=["540p","360p","720p"]

        if resolution not in ["540p","360p","720p"]:
            resolution="540p"


    
    payload={
    "pixverse/pixverse-v5-effects":{
        "duration": duration,
        "effect":effect,
        "image": image,
        "resolution": resolution,
        "sound_effect_switch":sound_effect_switch
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
    },
    "video-effects/shake-dance":{
        "image":image
    },
    "video-effects/romantic-lift":{
        "image":image
    },
    "video-effects/jiggle-up":{
        "image":image
    },
    "video-effects/pubg-winner-hit":{
        "bgm":bgm,
        "image":image
    },
    "video-effects/flying":{
        "image":image,
        
    },
    "video-effects/balloon-flyaway":{
        "image":image
    },
    "video-effects/blueprint-supreme":{
        "image":image,
        "bgm":bgm
    },
    "video-effects/flame-carpet":{
        "image":image
    },
    "video-effects/muscling":{
       "image":image
    },
    "video-effects/couple-arrival":{
       "image":image
    },
    "video-effects/ghibli":{
       "image":image
    },
    "video-effects/hugging":{
       "image":image
    },
    "video-effects/subject-3":{
       "image":image,
       "bgm":bgm
    },
    "video-effects/zoom-out":{
       "image":image
    },
    "video-effects/captain-america":{
       "image":image
    },
    "video-effects/cartoon-doll":{
       "image":image
    },
    "video-effects/fairy-me":{
       "image":image
    },
    "video-effects/fashion-stride":{
       "image":image
    },
    "video-effects/fishermen":{
       "image":image
    },
    "video-effects/fluffy-plunge":{
       "image":image
    },
    "video-effects/gender-swap":{
       "image":image
    },
    "video-effects/golden-epoch":{
       "image":image
    },
    "video-effects/live-memory":{
       "image":image
    },
    "video-effects/melt":{
       "image":image
    },
    "video-effects/pilot":{
       "image":image
    },
    "video-effects/sweet-proposal":{
       "image":image
    },
    "video-effects/toy-me":{
       "image":image
    },
    "vidu/template/halloween":{
       "image":image,
       "template":template,
       "seed":seed,
       "bgm":bgm
    },
    "video-effects/break-glass":{
        "image":image
    },
    "video-effects/cap-walk":{
        "image":image
    },
    "video-effects/carry-me":{
        "image":image
    },
    "video-effects/child-memory":{
        "image":image
    },
    "video-effects/claysho":{
        "image":image
    },
    "video-effects/couple-hugging":{
        "image":image
    },
    "video-effects/exotic-princess":{
        "image":image
    },
    "video-effects/flower-receive":{
        "image":image
    },
    "video-effects/hulk":{
        "image":image
    },
    "video-effects/hulk-dive":{
        "image":image
    },
    "video-effects/paperman":{
        "image":image
    },
    "video-effects/nap-me-360p":{
        "image":image
    },
    "video-effects/minecraft":{
        "image":image
    },
    "video-effects/ladudu-me-random":{
        "image":image
    },
    "video-effects/past-life-job":{
        "image":image
    },
    "video-effects/pet-lovers":{
        "image":image
    },
    "video-effects/pinch":{
        "image":image
    },
    "video-effects/pixel-me":{
        "image":image
    },
    "video-effects/slice-therapy":{
        "image":image
    },
    "video-effects/soul-depart":{
        "image":image
    },
    "video-effects/split-stance-human":{
        "image":image
    },
    "video-effects/star-carpet":{
        "image":image
    },
    "video-effects/tap-me":{
        "image":image
    },
    "video-effects/zoom-in-fast":{
        "image":image
    },
    "video-effects/dreamy-wedding":{
        "image":image
    },
    "video-effects/dust-me-away":{
        "image":image,
        "resolution":resolution
    },
    "video-effects/hair-swap":{
        "image":image
    },
    "video-effects/manga-meme":{
        "image":image
    },
    "video-effects/oscar-gala":{
        "image":image
    },
    "video-effects/red-or-white":{
        "image":image,
        "resolution":resolution
    },
    "video-effects/squid-game":{
        "image":image,
        "bgm":bgm
    },
    "video-effects/walk-forward":{
        "image":image
    }

    }
    # print("payload",payload[model_id])
    data = payload.get(model_id)
    if data is not None:
      return data
    return None


