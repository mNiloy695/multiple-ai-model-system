def payload_data(model_id,duration=None,effect=None,image=None,resolution=None,bgm=False,template="sexy_devil",seed=0):

    print("model is is ",model_id)


    if model_id=="vidu/template/halloween":
        template_list = ["tim_burton","broomstick_fly","witchy_pet","pumpkin_head","sexy_devil","dance_with_ghost","crow_arrival","clown_makeup","shadow_of_terror_video","not_look_back_video","turn_into_zombie","head_to_balloon","covered_liquid_metal","wednesdays_vibe"]
        if template not in template_list:
             template="sexy_devil"
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
    }
    }
    # print("payload",payload[model_id])
    data = payload.get(model_id)
    if data is not None:
      return data
    return None


