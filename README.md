# 🩺 NHS Paperwork Automation Agent

An AI-powered solution to automate NHS clinical form generation, reducing administrative burden on healthcare professionals.

## 🎯 Problem Statement

Clinicians and support workers in the NHS spend countless hours filling out repetitive forms (referrals, discharge summaries, risk assessments, compliance checks), leading to:
- Clinician burnout
- Reduced patient-facing time  
- Administrative delays

## 💡 Solution

An AI Agent that:
- ✅ **Listens/ingests** clinician notes (speech-to-text or uploaded text)
- ✅ **Extracts structured data** (patient details, diagnosis, medications)
- ✅ **Auto-fills NHS standard forms** (referral, discharge, compliance)
- ✅ **Exports to PDF/Word** format for submission
- ✅ **Suggests missing info** and flags compliance gaps

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI        │    │   AI Services   │
│   Dashboard     │◄──►│   Backend        │◄──►│   OpenAI GPT-4  │
│                 │    │                  │    │   Whisper STT   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   SQLite/        │
                       │   PostgreSQL     │
                       │   Database       │
                       └──────────────────┘
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone and navigate to project
cd nhs-paperwork-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
copy .env.template .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Demo

```bash
# Test the core functionality
python demo.py
```

### 4. Start the Application

**Terminal 1 - API Backend:**
```bash
python start_api.py
```

**Terminal 2 - Web Dashboard:**
```bash
python start_dashboard.py
```

Then open http://localhost:8501 in your browser.

## 📋 Features

### ✅ **Core MVP Features (Implemented)**

- **🧠 AI Data Extraction**: Uses OpenAI GPT-4 to extract structured data from clinical notes
- **📝 Form Auto-Fill**: Automatically fills NHS standard forms (Discharge Summary, Referral, Risk Assessment)
- **🎙️ Speech-to-Text**: Transcribes audio recordings using OpenAI Whisper
- **📄 PDF Generation**: Exports forms as professional NHS-compliant PDFs
- **🖥️ Web Dashboard**: User-friendly Streamlit interface
- **🔧 REST API**: FastAPI backend with comprehensive endpoints

### 🔄 **Coming Soon**

- **💾 Database Persistence**: Full data storage and retrieval
- **👥 Multi-user Support**: User accounts and session management
- **💳 Subscription Billing**: Freemium model with Stripe integration
- **🔒 Enhanced Security**: End-to-end encryption, audit logging
- **🏥 EHR Integration**: FHIR APIs for EMIS, EPIC, Cerner

## 📁 Project Structure

```
nhs-paperwork-agent/
├── src/
│   ├── models/          # Data models (Pydantic & SQLAlchemy)
│   ├── services/        # Core business logic
│   │   ├── nlp_extraction.py    # AI data extraction
│   │   ├── form_templates.py    # NHS form definitions  
│   │   ├── form_filler.py       # Auto-fill engine
│   │   └── pdf_generator.py     # PDF export
│   ├── api/             # FastAPI REST endpoints
│   ├── dashboard/       # Streamlit web interface
│   └── core/           # Configuration & database
├── templates/          # Form templates
├── data/              # SQLite database & generated files
├── tests/             # Unit tests
└── docs/              # Documentation
```

## 🧪 Testing

### Run Demo with Sample Data

```bash
python demo.py
```

This will:
1. Process a sample clinical note
2. Extract structured data using AI
3. Generate NHS forms automatically  
4. Create PDF documents
5. Show confidence scores and suggestions

### API Testing

```bash
# Start API server
python start_api.py

# In another terminal, test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/templates
```

## 🏥 Supported NHS Forms

| Form Type | Status | Description |
|-----------|--------|-------------|
| **Discharge Summary** | ✅ Complete | Patient discharge documentation |
| **Referral Form** | ✅ Complete | Inter-departmental referrals |
| **Risk Assessment** | ✅ Complete | Falls, pressure ulcer, mental health risks |
| **GP Letter** | 🔄 Planned | Communication with general practitioners |
| **Compliance Check** | 🔄 Planned | Regulatory compliance verification |

## 🤖 AI Capabilities

### Data Extraction
- **Patient Demographics**: Name, NHS number, DOB, address, GP details
- **Clinical Information**: Diagnoses, medications, allergies, examination findings
- **Treatment Details**: Procedures, medications, follow-up plans
- **Risk Factors**: Falls risk, pressure ulcer risk, mental health concerns

### Confidence Scoring
- Provides extraction confidence percentage
- Identifies missing critical fields
- Suggests questions to gather missing information

### Medical Terminology
- Understands NHS clinical terminology
- Maintains medical accuracy in extractions
- Preserves clinical context and relationships

## 🔒 NHS Compliance & Security

### Data Protection
- GDPR compliant data handling
- NHS Data Security Standards alignment
- Configurable data retention policies
- Audit logging for all operations

### Security Features
- End-to-end encryption for sensitive data
- Secure API authentication (planned)
- Session management and access controls
- Compliance reporting dashboard

## 💼 Business Model

### Target Users
- **🏥 NHS Trusts**: Enterprise B2B SaaS deployment
- **🏢 Private Clinics & Care Homes**: Professional subscriptions  
- **👨‍⚕️ Individual Clinicians**: Freelance nurses, locums, GPs

### Pricing Tiers
- **🆓 Freemium**: 10 forms/month, basic features
- **💎 Pro (£49-99/month)**: Unlimited forms, speech-to-text, EHR integration
- **🏢 Enterprise (£500-2000/month)**: Multi-user, compliance reports, priority support

## 🛠️ Development

### Adding New Form Types

1. **Define Form Template**:
```python
# In src/services/form_templates.py
def _create_new_form_template(self) -> FormTemplate:
    fields = [
        FormField(field_id="...", field_name="...", field_type="...")
    ]
    return FormTemplate(form_id="...", fields=fields)
```

2. **Add Mapping Logic**:
```python
# In src/services/form_filler.py  
def _map_new_form(self, data: ExtractedData) -> Dict[str, Any]:
    return {"field_id": "mapped_value"}
```

3. **Add PDF Template**:
```python
# In src/services/pdf_generator.py
def _build_new_form_content(self, data: Dict[str, Any]) -> list:
    # Build PDF content structure
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 and Whisper | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///./data/nhs_agent.db` |
| `DEBUG` | Enable debug mode | `False` |
| `SECRET_KEY` | JWT secret key | Generated |

## 🧪 Example Usage

### Clinical Note Input
```
Patient: Smith, John
NHS Number: 1234567890
DOB: 15/03/1965
Presenting complaint: Chest pain for 2 days
History: 65-year-old male with hypertension and diabetes...
Medications: Amlodipine 5mg OD, Metformin 500mg BD
Allergies: Penicillin
Discharge plan: Cardiology follow-up in 6 weeks
```

### AI Output
```json
{
  "patient": {
    "first_name": "John",
    "last_name": "Smith", 
    "nhs_number": "1234567890",
    "date_of_birth": "1965-03-15"
  },
  "clinical": {
    "primary_diagnosis": "Acute myocardial infarction",
    "medications": [
      {"name": "Amlodipine", "dose": "5mg", "frequency": "once daily"}
    ],
    "allergies": ["Penicillin"]
  }
}
```

## 🚀 Deployment

### Development
```bash
# API Server
python start_api.py

# Dashboard  
python start_dashboard.py
```

### Production (Docker)
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 📊 Roadmap

### Month 1 (Current - Prototype)
- ✅ Build agent: text notes → filled discharge form (PDF)
- ✅ Test with mock data
- ✅ Core AI extraction and form filling

### Month 2 (Pilot)
- 🔄 Add speech-to-text integration
- 🔄 Support 3+ form types
- 🔄 Deploy web dashboard
- 🔄 Database persistence

### Month 3 (Beta Launch)  
- 📋 Add subscription billing (Stripe)
- 📋 Onboard 5-10 test users
- 📋 Collect feedback on accuracy and speed
- 📋 NHS compliance certification

### Future Scaling
- 📈 Multi-form support (GP letters, compliance checklists)
- 📈 NHS system integration (EMIS, EPIC, Cerner via FHIR)
- 📈 Enterprise dashboard (analytics, audit logs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ⚠️ Important Notes

### For Development
- This is a prototype for demonstration purposes
- Requires OpenAI API key for AI features
- Uses mock NHS numbers in examples (not real patient data)
- SQLite database for development (migrate to PostgreSQL for production)

### For Production Deployment
- Implement proper NHS Data Security standards
- Add user authentication and authorization
- Configure production database (PostgreSQL)
- Set up SSL/TLS encryption
- Implement audit logging and compliance reporting
- Obtain necessary NHS certifications and approvals

## 📞 Support

For questions, issues, or collaboration opportunities:

- 📧 **Email**: [Chinedumazigtv@gmail.com]
- 💬 **Issues**: [GitHub Issues URL]
- 📚 **Documentation**: [Documentation URL]

---

**Built with ❤️ for NHS healthcare professionals**

Complete project work

<img width="2880" height="1518" alt="image" src="https://github.com/user-attachments/assets/c73723b1-3c6a-4a49-a6aa-c5338262ff22" />
