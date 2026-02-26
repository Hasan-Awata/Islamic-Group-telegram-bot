import re
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes

# Local imports
from class_khetma import Khetma

async def is_user_admin(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Checks if a user is an Admin or the Creator of the group.
    """
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        # Check if status is 'administrator' or 'creator'
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        # If user is not found or bot has no access, assume False
        return False

async def get_username(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    """
    Fetches the user's @username. If they don't have one, returns their First Name.
    """
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        user = member.user
        
        if user.username:
            return f"@{user.username}"
        else:
            return user.first_name
            
    except Exception:
        return "Unknown User"

def extract_arabic_numbers(text: str) -> list[int]:
    """
    Robustly extracts Arabic numbers, handling separated compound numbers
    like 'سبعة و عشرون' correctly.
    """
    
    # --- 1. CONFIGURATION & MAPPING ---
    
    # Arabic-Indic to Western (٠-٩ -> 0-9)
    arabic_indic_map = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    
    # Map normalized words to values
    # Note: 'ة' is normalized to 'ه', 'ى' to 'ي', 'أ/إ' to 'ا'
    num_map = {
        # Units (1-9)
        'صفر': 0,
        'واحد': 1, 'واحده': 1, 'احد': 1, 'حادي': 1, 'اول': 1, 'اولي': 1,
        'اثنان': 2, 'اثنين': 2, 'ثاني': 2, 'ثانيه': 2,
        'ثلاث': 3, 'ثلاثه': 3, 'ثالث': 3, 'ثالثه': 3,
        'اربع': 4, 'ارابعه': 4, 'رابع': 4, 'رابعه': 4,
        'خمس': 5, 'خمسه': 5, 'خامس': 5, 'خامسه': 5,
        'ست': 6, 'سته': 6, 'سادس': 6, 'سادسه': 6,
        'سبع': 7, 'سبعه': 7, 'سابع': 7, 'سابعه': 7,
        'ثمان': 8, 'ثمانيه': 8, 'ثامن': 8, 'ثامنه': 8,
        'تسع': 9, 'تسعه': 9, 'تاسع': 9, 'تاسعه': 9,
        
        # 10 is special (Context dependent)
        'عشر': 10, 'عشره': 10, 'عاشر': 10, 'عاشره': 10,
        
        # Tens (20-90)
        'عشرون': 20, 'عشرين': 20,
        'ثلاثون': 30, 'ثلاثين': 30,
        'اربعون': 40, 'اربعين': 40,
        'خمسون': 50, 'خمسين': 50,
        'ستون': 60, 'ستين': 60,
        'سبعون': 70, 'سبعين': 70,
        'ثمانون': 80, 'ثمانين': 80,
        'تسعون': 90, 'تسعين': 90,
        
        # Large
        'مائه': 100, 'مئه': 100, 'الف': 1000, 'مليون': 1000000
    }

    # --- 2. NORMALIZATION ---
    
    # 1. Translate Digits
    text = text.translate(arabic_indic_map)
    
    # 2. Normalize Characters
    text = re.sub(r'[أإآ]', 'ا', text)   # Alif
    text = re.sub(r'ة', 'ه', text)       # Ta Marbuta
    text = re.sub(r'ى', 'ي', text)       # Alif Maqsura (Fixes الأولى -> الاولي)
    text = re.sub(r'ـ', '', text)        # Tatweel
    
    # 3. Space out Digits (so "1و30" becomes "1 و 30")
    text = re.sub(r'(\d+)', r' \1 ', text)
    
    # 4. Standardize standalone "Wa" (ensure spaces around it)
    text = re.sub(r'\s+و\s+', ' و ', text)

    tokens = text.split()
    results = []
    
    # --- 3. STATE MACHINE ---
    
    pending_unit = None  # Stores a number like 7 waiting for a 20
    saw_wa = False       # Flag: Did we just see a "Wa"?

    def flush_pending():
        """Helper: Pushes the pending unit to results and clears it."""
        nonlocal pending_unit, saw_wa
        if pending_unit is not None:
            results.append(pending_unit)
            pending_unit = None
        saw_wa = False

    for token in tokens:
        
        # --- A. Handle Digits (1, 30, 100) ---
        if token.isdigit():
            flush_pending() # Digits break any text flow
            results.append(int(token))
            continue
            
        # --- B. Clean Word ---
        word = token
        word_had_wa = False
        
        # Strip 'Wa' if attached (e.g. "والعشرون")
        if word.startswith('و') and len(word) > 1 and word not in ['واحد', 'واحده']:
            word = word[1:]
            word_had_wa = True
        
        # Strip 'Al' (e.g. "العشرون")
        if word.startswith('ال'):
            word = word[2:]
            
        # Lookup
        val = num_map.get(word)
        
        # --- C. Handle "Wa" (The connector) ---
        if token == 'و':
            if pending_unit is not None:
                saw_wa = True # We have a 7, we see Wa, we wait for 20.
            continue # Skip to next token

        # --- D. Handle Logic ---
        if val is not None:
            
            # Case 1: The "Teen" numbers (11-19)
            # Logic: We have a Unit (1-9), and we see 10. (e.g. "Sab'at Ashar")
            if val == 10 and pending_unit is not None:
                results.append(pending_unit + 10)
                pending_unit = None
                saw_wa = False
                
            # Case 2: The "Ten" numbers (21-99)
            # Logic: We have a Unit (1-9), we saw 'Wa', and we see 20-90.
            elif val >= 20 and pending_unit is not None and (saw_wa or word_had_wa):
                results.append(pending_unit + val)
                pending_unit = None
                saw_wa = False
                
            # Case 3: Just a Unit (1-9) or a new Ten (20)
            else:
                # If we had a previous unit pending (e.g. "Part 3... Part 5"), flush the old one.
                flush_pending()
                
                # If it's a Unit, store it and wait. (It might be 7... + 20)
                if val < 10:
                    pending_unit = val
                # If it's a standalone Ten (e.g. "Chapter Twenty"), just add it.
                else:
                    results.append(val)
        
        else:
            # Word is garbage (e.g. "Juz", "Page")
            flush_pending()

    # Final cleanup
    flush_pending()
    
    return results

# --- VALIDATION ---
test_text = """
1- الجزء الأول 
2- الجزء السابع والعشرون
3- الجزء السابع و العشرون
4- الجزء السابع والعشرين
5- الجزء 1و30
6- الجزء 3 و5
7- الحادي عشر
8- الأحد عشر
9- الاحد عشر
10- ٢٥ (Arabic-Indic 25)
11- ٢ (Arabic 2)
12- خمسة وسبعون
13- الأولى
"""

def number_to_ordinal_arabic(n: int) -> str:
    """
    Converts integer to Arabic Ordinal string (Nominative Case).
    Corrects 'First' vs 'Hadi' logic.
    Example: 
    1 -> الأول 
    11 -> الحادي عشر
    21 -> الحادي والعشرون
    """
    if n < 1: return str(n)

    # 1. Base Units (with Al-)
    # Note: We don't put 'Al-Awwal' here because it changes in compounds.
    units_map = {
        2: "الثاني", 3: "الثالث", 4: "الرابع", 5: "الخامس",
        6: "السادس", 7: "السابع", 8: "الثامن", 9: "التاسع", 10: "العاشر"
    }

    # 2. Tens (Nominative Case - Marfu' with Waw)
    tens_map = {
        20: "العشرون", 30: "الثلاثون", 40: "الأربعون", 50: "الخمسون",
        60: "الستون", 70: "السبعون", 80: "الثمانون", 90: "التسعون"
    }

    # --- LOGIC ---

    # Case A: 1st (Special Case)
    if n == 1:
        return "الأول"

    # Case B: 2nd to 10th
    if n <= 10:
        return units_map[n]

    # Case C: 11-19 (The Teens)
    if n < 20:
        # Determine the unit part
        if n == 11:
            unit_part = "الحادي" # Special rule for 11
        else:
            unit_part = units_map[n - 10]
        
        return f"{unit_part} عشر"

    # Case D: Exact Tens (20, 30...)
    if n % 10 == 0:
        return tens_map[n]

    # Case E: Compound Numbers (21-99)
    # Rule: Unit + "Wa" + Ten
    unit = n % 10
    ten = n - unit
    
    # 1. Handle the Unit part
    if unit == 1:
        unit_str = "الحادي" # Rule: Use 'Hadi' in compounds, not 'Awwal'
    else:
        unit_str = units_map[unit]
        
    # 2. Handle the Ten part
    ten_str = tens_map[ten]
    
    return f"{unit_str} و{ten_str}"


def create_khetma_message(khetma: Khetma) -> str:
    chapters_text = ""

    for chapter in khetma.chapters:
        # Handle chapter status
        if chapter.status.value == "FINISHED":
            status = "✅"
        elif chapter.status.value == "RESERVED":
            status = f"{chapter.owner_username}"  
        else:
            status = "" 

        # Build the line
        chapters_text += f"الجزء {number_to_ordinal_arabic(chapter.number)} : {status}\n"

    # Construct the final block
    message = (
        f"**الختمة رقم -> {khetma.number}**"
        f"**الحالة: {"مستمرة" if khetma.status.value == "ACTIVE" else "منتهية"}**"
        f"\n------------------\n"
        f"{chapters_text}"
    )
    
    return message  