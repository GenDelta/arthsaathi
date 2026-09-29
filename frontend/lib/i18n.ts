export type Language = "en" | "hi";

export const translations = {
  en: {
    auth: {
      subtitle: "Enter your mobile number to continue",
      scanSubtitle: "Scan this QR code with Google Authenticator or Authy",
      verifySubtitle: "Enter the 6-digit code from your authenticator app",
      phone: "Mobile Number (e.g. 9876543210)",
      continue: "Continue",
      totpExplainer: "ArthSaathi uses an authenticator app for secure, free sign-in. No SMS charges.",
      scanInstructions: "Open Google Authenticator or Authy, tap '+', then scan this QR code. You only do this once.",
      manualEntry: "Can't scan? Enter code manually",
      scannedIt: "I've scanned it — Continue",
      enterCode: "Enter the 6-digit code shown in your authenticator app",
      verifyAndLogin: "Verify & Sign In",
      newDevice: "Using a new device? Re-scan QR code",
      invalidPhone: "Please enter a valid 10-digit mobile number.",
      invalidCode: "Please enter a valid 6-digit authenticator code.",
    },
    common: {
      loading: "Loading...",
      switchTo: "🇮🇳 हिंदी",
      error: "Something went wrong. Please try again."
    },
    dashboard: {
      hello: "Hello",
      totalIncome: "Total Income",
      totalExpenses: "Total Expenses",
      netSavings: "Net Savings",
      thisMonth: "this month",
      guardianInsights: "Guardian Insights",
      new: "New",
      review: "Review",
      saveNow: "Save Now",
      dismiss: "Dismiss",
      recentActivity: "Recent Activity",
      viewAll: "View All"
    },
    scanner: {
      title: "Scam Scanner",
      subtitle: "Upload a contract or loan document to check for predatory clauses.",
      tapUpload: "Tap to upload document",
      supportText: "Supports PDF, JPG, and PNG files up to 5MB. Clear, legible images work best.",
      chooseFile: "Choose File",
      analyzing: "Analyzing document...",
      highRisk: "High Risk Detected",
      score: "Score",
      riskText: "This document contains clauses that strongly match known predatory lending patterns. We recommend consulting a legal aid NGO before signing.",
      flagged: "Flagged Clauses",
      scanAnother: "Scan another document"
    },
    onboarding: {
      typing: "ArthSaathi is typing...",
      placeholder: "Type your message here...",
      send: "Send",
      complete: "Profile setup complete! Redirecting...",
    }
  },
  hi: {
    auth: {
      subtitle: "जारी रखने के लिए अपना मोबाइल नंबर दर्ज करें",
      scanSubtitle: "Google Authenticator या Authy से यह QR कोड स्कैन करें",
      verifySubtitle: "अपने authenticator app का 6-अंकीय कोड दर्ज करें",
      phone: "मोबाइल नंबर (उदा. 9876543210)",
      continue: "जारी रखें",
      totpExplainer: "ArthSaathi सुरक्षित और मुफ्त लॉगिन के लिए authenticator app का उपयोग करता है। कोई SMS शुल्क नहीं।",
      scanInstructions: "Google Authenticator या Authy खोलें, '+' दबाएं, फिर यह QR कोड स्कैन करें। यह केवल एक बार करना है।",
      manualEntry: "स्कैन नहीं कर सकते? कोड मैन्युअल दर्ज करें",
      scannedIt: "स्कैन कर लिया — जारी रखें",
      enterCode: "अपने authenticator app में दिखा 6-अंकीय कोड दर्ज करें",
      verifyAndLogin: "सत्यापित करें और लॉगिन करें",
      newDevice: "नया डिवाइस? QR कोड फिर से स्कैन करें",
      invalidPhone: "कृपया एक वैध 10-अंकीय मोबाइल नंबर दर्ज करें।",
      invalidCode: "कृपया एक वैध 6-अंकीय ऑथेंटिकेटर कोड दर्ज करें।",
    },
    common: {
      loading: "लोड हो रहा है...",
      switchTo: "🇬🇧 English",
      error: "कुछ गलत हो गया। कृपया पुन: प्रयास करें।"
    },
    dashboard: {
      hello: "नमस्ते",
      totalIncome: "कुल आय",
      totalExpenses: "कुल खर्च",
      netSavings: "शुद्ध बचत",
      thisMonth: "इस महीने",
      guardianInsights: "गार्जियन इनसाइट्स",
      new: "नया",
      review: "समीक्षा करें",
      saveNow: "अभी सहेजें",
      dismiss: "खारिज करें",
      recentActivity: "हाल की गतिविधि",
      viewAll: "सभी देखें"
    },
    scanner: {
      title: "घोटाला स्कैनर",
      subtitle: "शिकारी खंडों की जांच करने के लिए अनुबंध या ऋण दस्तावेज अपलोड करें।",
      tapUpload: "दस्तावेज़ अपलोड करने के लिए टैप करें",
      supportText: "5MB तक के PDF, JPG और PNG फ़ाइलों का समर्थन करता है। स्पष्ट, सुपाठ्य चित्र सबसे अच्छा काम करते हैं।",
      chooseFile: "फ़ाइल चुनें",
      analyzing: "दस्तावेज़ का विश्लेषण हो रहा है...",
      highRisk: "उच्च जोखिम पाया गया",
      score: "स्कोर",
      riskText: "इस दस्तावेज़ में ऐसे खंड हैं जो ज्ञात शिकारी ऋण पैटर्न से दृढ़ता से मेल खाते हैं। हम हस्ताक्षर करने से पहले किसी कानूनी सहायता NGO से परामर्श करने की सलाह देते हैं।",
      flagged: "चिह्नित खंड",
      scanAnother: "एक और दस्तावेज़ स्कैन करें"
    },
    onboarding: {
      typing: "अर्थसाथी लिख रहा है...",
      placeholder: "अपना संदेश यहाँ लिखें...",
      send: "भेजें",
      complete: "प्रोफ़ाइल सेटअप पूरा हुआ! आपको ले जा रहे हैं...",
    }
  }
};
