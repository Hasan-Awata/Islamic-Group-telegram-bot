# ==========================================
# BASE ERROR
# ==========================================
class KhetmaError(Exception):
    """
    Base class for all Khetma-related exceptions.
    Catch this to handle ANY error gracefully.
    """
    def __init__(self, message="⚠️ حدث خطأ غير متوقع في النظام."):
        self.message = message
        super().__init__(self.message)

# ==========================================
# 1. RESERVATION RULES (Taking a Chapter)
# ==========================================
class ChapterAlreadyReservedError(KhetmaError):
    """Raised when user clicks a button that someone else just took."""
    def __init__(self, message="⛔ عذراً، هذا الجزء تم حجزه مسبقاً من قبل شخص آخر."):
        super().__init__(message)

class UserHasActiveChapterError(KhetmaError):
    """Raised when user tries to take a 2nd chapter before finishing the 1st."""
    def __init__(self, message="✋ لديك جزء لم تنتهِ منه بعد! الرجاء إتمام جزئك الحالي أولاً."):
        super().__init__(message)

class ChapterFinishedError(KhetmaError):
    """Raised when trying to reserve a chapter that is already done."""
    def __init__(self, message="✅ هذا الجزء قد تم الانتهاء منه بالفعل، جزاكم الله خيراً."):
        super().__init__(message)

# ==========================================
# 2. MODIFICATION RULES (Withdrawing/Finishing)
# ==========================================
class ChapterNotOwnedError(KhetmaError):
    """Raised when user tries to 'Finish' a chapter they don't own."""
    def __init__(self, message="⛔ عذراً، هذا الجزء ليس محجوزاً باسمك."):
        super().__init__(message)

class ChapterAlreadyEmptyError(KhetmaError):
    """Raised when trying to withdraw/cancel a chapter that is already free."""
    def __init__(self, message="⚠️ هذا الجزء غير محجوز أصلاً."):
        super().__init__(message)

class KhetmaNotSpecifiedError(KhetmaError):
    """Raised when trying to finish/withdraw/cancel a chapter wihtout specifying its khetma message."""
    def __init__(self, message="⚠️ الرجاء الرد على رسالة الختمة المقصودة"):
        super().__init__(message)

class NoOwnedChapters(KhetmaError):
    """Raised when trying to finish/withdraw/cancel a chapter wihtout owning any chapters."""
    def __init__(self, message="لا يوجد أي أجزاء محجوزة باسمك ⛔"):
        super().__init__(message)

# ==========================================
# 3. CONTEXT & STATE (Old Messages)
# ==========================================
class KhetmaNotFoundError(KhetmaError):
    """Raised when the Khetma ID in the button doesn't exist in DB (Old message)."""
    def __init__(self, message="❌ هذه الختمة لم تعد موجودة."):
        super().__init__(message)

class KhetmaCompletedError(KhetmaError):
    """Raised when trying to interact with a Khetma that is fully finished."""
    def __init__(self, message="🎉 تم اكتمال هذه الختمة بالكامل! انتظر الختمة الجديدة."):
        super().__init__(message)

class MessageExpiredError(KhetmaError):
    """Raised when interacting with a message from a deleted/old chat session."""
    def __init__(self, message="⌛ هذه الرسالة قديمة، يرجى استخدام القائمة الجديدة."):
        super().__init__(message)

# ==========================================
# 4. SECURITY & SPAM (Protection)
# ==========================================
class NotAdminError(KhetmaError):
    """Raised when a non-admin tries to use admin controls."""
    def __init__(self, message="🔒 عذراً، هذا الأمر متاح للمشرفين فقط."):
        super().__init__(message)

class RateLimitError(KhetmaError):
    """Raised when a user clicks buttons too fast (Spam Protection)."""
    def __init__(self, message="⏳ الرجاء الانتظار قليلاً قبل المحاولة مرة أخرى."):
        super().__init__(message)

# ==========================================
# 5. SYSTEM FAILURES (Backend)
# ==========================================
class DatabaseConnectionError(KhetmaError):
    """Raised when PostgreSQL fails or locks up."""
    def __init__(self, message="⚠️ خطأ في قاعدة البيانات، حاول مرة أخرى لاحقاً."):
        super().__init__(message)

class BotMaintenanceError(KhetmaError):
    """Raised if you add a 'Maintenance Mode' switch later."""
    def __init__(self, message="🛠️ البوت في وضع الصيانة حالياً، سنعود قريباً!"):
        super().__init__(message)