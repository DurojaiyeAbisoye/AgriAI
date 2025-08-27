from transformers import pipeline

MODEL_NAME = "facebook/nllb-200-distilled-600M"#"facebook/nllb-200-3.3B"
def translate_text(text, source_lang="eng_Latn", target_lang="yor_Latn"):
    translator = pipeline("translation", model=MODEL_NAME, src_lang=source_lang, tgt_lang=target_lang)
    translation = translator(text, max_length=512)
    return translation[0]['translation_text']


def translate_disease_info(disease_info, target_lang='yor_Latn'):
    translated_info = {}
    for key, value in disease_info.items():
        if isinstance(value, list):
            translated_list = [translate_text(item, target_lang=target_lang) for item in value]
            translated_info[key] = translated_list
        else:
            translated_info[key] = translate_text(value, target_lang=target_lang)
    return translated_info