from typing import List
import regex
import pdb

def get_bracketed_split(split_text: str) -> str:
    increase = "<([{"
    decrease = ">)]}"
    blevel = -1
    items = [[]]
    split_now = False
    start_bracket = False
    for char in split_text:
        if char in increase:
            blevel += 1
            if blevel == 0:
                start_bracket = True
                split_now = True
        elif char in decrease:
            blevel -= 1
            if blevel == -1:
                start_bracket = False
                split_now = True
        if split_now:
            if not start_bracket:
                items[-1].append(char)
            if len(items[-1]) != 0:
                items[-1] = "".join(items[-1]).strip()
                items.append([])
            if start_bracket:
                items[-1].append(char)
        else:
            items[-1].append(char)
        split_now = False
    if items[-1] == []:
        items.pop()
    else:
        items[-1] = "".join(items[-1]).strip()
    return items

def split_id(split_text: str) -> List[str]:
    out = get_bracketed_split(split_text)
    return out

def get_bracketed_list_items(split_text: str, split_chars: str) -> str:
    increase = "<([{"
    decrease = ">)]}"
    blevel = -1
    items = [[]]
    for char in split_text:
        if char in increase:
            blevel += 1
            continue
        elif char in decrease:
            blevel -= 1
            continue
        elif char == "," and blevel == 0:
            items[-1] = "".join(items[-1]).strip()
            items.append([])
            continue
        else:
            items[-1].append(char)
            continue
    if items[-1] == []:
        items.pop()
    else:
        items[-1] = "".join(items[-1]).strip()
    return items

def form_id(parts: List[str]) -> str:
    return "".join(parts)
