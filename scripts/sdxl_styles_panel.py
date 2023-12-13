import contextlib

import gradio as gr
from modules import scripts, shared, script_callbacks
from modules.ui_components import FormRow, FormColumn, FormGroup, ToolButton
import json
import os
import random

available_styles = {}
available_modes = ["Enable SDXL styles", "Disable SDXL styles"] # TODO: Random styles (per processing, per batch), Try all styles

def read_sdxl_styles_from_json(json_data):
    # Check that data is a list
    if not isinstance(json_data, list):
        print("[!] Error: input data must be a list (invalid style JSON format)")
        return None

    names = []

    # Iterate over each item in the data list
    for item in json_data:
        # Check that the item is a dictionary
        if isinstance(item, dict):
            # Check that 'name' is a key in the dictionary
            if 'name' in item:
                # Append the value of 'name' to the names list
                names.append(item['name'])
                available_styles[item["name"]] = item


def read_sdxl_styles():

    print("[i] Updating SDXL styles from storage ...")
    styles_dir = os.path.join(scripts.basedir(), "styles")

    for filename in os.listdir(styles_dir):
        if filename.endswith(".json"):
            print("[i] Reading SDXL styles from " + str(filename) + " ...")
            json_path = os.path.join(styles_dir, filename)

            try:
                with open(json_path, 'rt', encoding="utf-8") as file:
                    json_data = json.load(file)
                    read_sdxl_styles_from_json(json_data)

            except Exception as e:
                print(f"[!] A Problem occurred: {str(e)}")

    print("[i] Loaded " + str(len(available_styles)) + " styles!")


def apply_styles(styles, type, prompt):
    try:

        if not prompt:
            print("[w] Prompt of type " + type + " was null!")
            prompt = ""

        for name in styles:
            template = available_styles[name].get(type, "{prompt}")

            if template is None:
                print("[w] Fixing null template for " + name)
                template = "{prompt}"

            # Add missing prompt expansion
            if not ("{prompt}" in template):
                print("[w] Fixing missing expansion term in template for " + name)
                template = template + ", {prompt}"

            # Replace prompt
            prompt = template.replace("{prompt}", prompt)

        return prompt

    except Exception as e:
        print(f"[!] An error occurred in apply_styles: {str(e)}")
        raise e


class SDXLStylesPanel(scripts.Script):
    def __init__(self) -> None:
        super().__init__()
        
    # Cache all styles
    read_sdxl_styles()

    def title(self):
        return "SDXL Multi-Style Selector"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Group():
            with gr.Accordion("SDXL Styles", open=False):
                with FormRow():
                    with FormColumn(min_width=160):
                        mode = gr.Dropdown(choices=available_modes, value=available_modes[0], multiselect=False, label="Mode selection")

                styles = gr.Dropdown(choices=sorted(available_styles), multiselect=True, label="Selected style(s)")

        return [mode, styles]

    def process(self, p, mode, styles):
        if mode == "Disable SDXL styles":
            print("[i] SDXL Styles are disabled.")
            return

        # for each image in batch TODO: randomization
        for i, prompt in enumerate(p.all_prompts):
            positivePrompt = apply_styles(styles, "prompt", prompt)
            p.all_prompts[i] = positivePrompt
            print("[i] SDXL Styles: Positive prompt #" + str(i + 1) + ": " + positivePrompt)

        for i, prompt in enumerate(p.all_negative_prompts):
            negativePrompt = apply_styles(styles, "negative_prompt", prompt)
            p.all_negative_prompts[i] = negativePrompt
            print("[i] SDXL Styles: Negative prompt #" + str(i + 1) + ": " + negativePrompt)

        p.extra_generation_params["SDXL Style Mode"] = mode
        p.extra_generation_params["SDXL Styles"] = styles

    def after_component(self, component, **kwargs):
        # https://github.com/AUTOMATIC1111/stable-diffusion-webui/pull/7456#issuecomment-1414465888 helpful link
        # Find the text2img textbox component
        if kwargs.get("elem_id") == "txt2img_prompt":  # postive prompt textbox
            self.boxx = component
        # Find the img2img textbox component
        if kwargs.get("elem_id") == "img2img_prompt":  # postive prompt textbox
            self.boxxIMG = component

        # this code below  works as well, you can send negative prompt text box,provided you change the code a little
        # switch  self.boxx with  self.neg_prompt_boxTXT  and self.boxxIMG with self.neg_prompt_boxIMG

        # if kwargs.get("elem_id") == "txt2img_neg_prompt":
            #self.neg_prompt_boxTXT = component
        # if kwargs.get("elem_id") == "img2img_neg_prompt":
            #self.neg_prompt_boxIMG = component


# def on_ui_settings():
#     section = ("styleselector", "Style Selector")
#     shared.opts.add_option(
#         "enable_styleselector_by_default",
#         shared.OptionInfo(
#             False,
#             "Show Style Selector by default",
#             gr.Checkbox,
#             section=section
#             )
#     )
#
# script_callbacks.on_ui_settings(on_ui_settings)
