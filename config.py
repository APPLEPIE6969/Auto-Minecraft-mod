class Config:
    def __init__(self, gemini_api_key="", groq_api_key="", jules_api_key="", output_dir="./generated_mods"):
        self.gemini_api_key = gemini_api_key
        self.groq_api_key = groq_api_key
        self.jules_api_key = jules_api_key
        self.output_dir = output_dir
        self.gemini_model = "gemini-2.0-flash-exp"
        self.groq_model = "llama-3.3-70b-versatile"
        self.jules_model = "gemini-2.0-flash-exp"

    @property
    def has_gemini(self):
        return bool(self.gemini_api_key)

    @property
    def has_groq(self):
        return bool(self.groq_api_key)

    @property
    def has_jules(self):
        return bool(self.jules_api_key)
