# FinSight AI - Complete Architecture Analysis
**Date: March 24, 2026**  
**Status: Production-Ready with Connected Backend/Frontend**

---

## 📊 1. ALL API ENDPOINTS

### **Core Analysis Endpoints**

#### **POST /api/analyze** ⭐ PRIMARY ENDPOINT
- **Owner**: Margaret
- **Purpose**: Master endpoint for complete financial analysis
- **Request Body**:
  ```json
  {
    "sms_text": "string (multiple SMS separated by newlines)",
    "user_id": "string (default: 'demo-user')",
    "balance": "float (optional, current balance)"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "user_id": "string",
    "score": { score, label, color, message, pillars, summary },
    "days_to_zero": { days_remaining, daily_burn_rate, urgency, message },
    "patterns": { patterns[], count, top_pattern },
    "actions": [ { title, detail, impact, type, category, interswitch_action } ],
    "parse_summary": { sms_received, transactions_parsed, transactions_saved, parse_rate },
    "transactions": [ { amount, type, category, description, transaction_date, balance } ]
  }
  ```
- **Flow**:
  1. Validates & splits SMS by newline
  2. Parses SMS to extract transactions
  3. Saves to Supabase (non-blocking)
  4. Calculates financial score
  5. Predicts days to zero
  6. Detects behavior patterns
  7. Generates AI actions
  8. Returns complete analysis + transactions

---

#### **GET /api/history/{user_id}**
- **Purpose**: Retrieve all saved transactions & re-analyze without re-pasting SMS
- **Response**: Same structure as `/api/analyze` but from stored database

#### **POST /api/score**
- **Purpose**: Quick score calculation for transaction list
- **Request**:
  ```json
  {
    "transactions": [ { amount, type, category, description, transaction_date } ],
    "balance": "float (optional)"
  }
  ```
- **Response**:
  ```json
  {
    "score": { ... },
    "days_to_zero": { ... },
    "patterns": { ... }
  }
  ```

---

### **SMS Parsing Endpoints** (api/routes/parse.py)

#### **POST /api/parse/sms**
- **Purpose**: Parse single SMS message
- **Request**: `{ "sms_text": "string", "bank_type": "string (optional)" }`
- **Response**: Parsed transaction or error
- **Supported Banks**: Access Bank, GTBank, First Bank, Zenith, UBA

#### **POST /api/parse/sms/batch**
- **Purpose**: Batch parse multiple SMS messages
- **Request**: `{ "sms_text": "string (\\n\\n separated)", "bank_type": "string (optional)" }`
- **Response**: Batch results with statistics

#### **GET /api/parse/banks**
- **Purpose**: Get list of supported banks with examples
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "supported_banks": [
        { "code": "access", "name": "Access Bank", "example": "..." },
        { "code": "gt", "name": "GTBank", "example": "..." }
      ]
    }
  }
  ```

#### **GET /api/parse/demo**
- **Purpose**: Get demo SMS data for testing
- **Response**: Sample SMS text

---

### **CSV Parsing Endpoints**

#### **POST /api/parse/csv**
- **Purpose**: Parse uploaded CSV file
- **Request**: Form-data with file upload
- **Response**: Parsed transactions with statistics

#### **POST /api/parse/csv/text**
- **Purpose**: Parse CSV as text
- **Request**: `{ "csv_text": "string (Form)" }`
- **Response**: Parsed transactions with statistics

---

### **Savings & Bill Optimization Endpoints**

#### **POST /api/savings/plan**
- **Purpose**: Create savings plan for user
- **Request**:
  ```json
  {
    "amount": "float",
    "plan_type": "string",
    "user_profile": "dict (optional)"
  }
  ```
- **Response**: Savings plan details + Interswitch integration results

#### **POST /api/savings/analyze**
- **Purpose**: Analyze spending patterns & savings recommendations
- **Request**:
  ```json
  {
    "transactions": [ { ... } ],
    "user_profile": "dict (optional)"
  }
  ```
- **Response**: Savings analysis & recommendations

#### **POST /api/savings/bills/optimize**
- **Purpose**: Analyze recurring bills & optimization strategies
- **Request**: `{ "transactions": [ { ... } ] }`
- **Response**: Bill optimization recommendations

---

### **Health & Auth Endpoints**

#### **GET /api/health**
- **Purpose**: Service health check (keep Vercel warm)
- **Response**: `{ "status": "ok", "service": "FinSight AI", "version": "1.0.0" }`

#### **POST /api/auth/google**
- **Purpose**: Google OAuth sign-in
- **Request**: `{ "id_token": "string (from Google Sign-In)" }`
- **Response**: `{ "user_id", "email", "access_token" }`

#### **POST /api/auth/bank-setup**
- **Purpose**: Link user's bank account for Interswitch actions
- **Request**: `{ "user_id", "bank_name", "account_number", "bvn_last4" }`
- **Response**: `{ "success": true, "message": "Bank account linked" }`

---

### **Root Endpoint**

#### **GET /**
- **Purpose**: Service discovery
- **Response**: Service info + endpoint list

---

## 🎯 2. NEW BACKEND FEATURES (AI Insights & PDF Handling)

### **A. AI Insights Engine** (services/ai_actions.py)
**Owner**: Toby

#### **Function: `generate_genuine_actions()`**
- **Zero hardcoded strings** - every action is data-driven
- **Inputs**:
  - `score_result`: Financial health score breakdown
  - `days_result`: Days to zero prediction
  - `pattern_result`: Behavior patterns detected
  - `raw_transactions`: Full transaction list
  - `user_context`: Optional network/profile info

#### **Generated Action Types**:

1. **Spending Cut Actions** (High Impact)
   - Identifies highest spending category
   - Calculates 25% reduction impact
   - Extends runway with exact days gained
   - Example: *"You have 14 days of money left — cut Entertainment spending first"*

2. **Data Bundle Recommendations** (High/Medium Impact)
   - Detects network used (MTN, Airtel, Glo, 9Mobile)
   - Analyzes purchase frequency & patterns
   - Calculates annual savings
   - Example: *"You are overpaying for data — switch to MTN 5GB bundle"*

3. **Electricity Bill Automation** (Medium Impact)
   - Tracks electricity spending & frequency
   - Calculates optimal auto-payment amount
   - Reduces manual friction
   - Example: *"Pay electricity automatically — stop buying tokens in panic"*

4. **Post-Salary Savings Lock** (High Impact)
   - Detects post-income spending spike
   - Recommends locking 30% of income
   - Executes via Interswitch transfer
   - Example: *"Lock ₦45,000 the moment your salary arrives"*

5. **Weekend Spending Cap** (High/Medium Impact)
   - Compares weekend vs weekday spending
   - Proposes sustainable cap (10% above weekday)
   - Projects monthly/annual savings
   - Example: *"Cap weekend spending at ₦8,000/day"*

6. **Bill Optimization** (Medium Impact)
   - Targets DSTV/GoTV subscriptions
   - Recommends auto-pay via Interswitch
   - Prevents subscription lapses

---

### **B. PDF Statement Parser** (finsight-pdf/main.py)
**Owner**: Margaret

#### **Supported Banks** (13 Nigerian Banks):
- UBA, GTBank, Access, Zenith, FirstBank
- Stanbic, Fidelity, Sterling, Polaris, FCMB, Wema, Ecobank
- Custom CSV import

#### **Features**:
- **PDF Parsing**: Uses `pdfplumber` to extract tables
- **Encrypted PDF Support**: Handles password-protected statements via `pikepdf`
- **Bank-Specific Parsing**: Config-driven extraction (date, amount, description, balance)
- **AI-Powered Insights**: Uses Groq AI to analyze extracted transactions
- **Supabase Storage**: Saves parsed statements & AI insights

#### **API Endpoints** (finsight-pdf):
```
POST /api/statements/upload
  - Upload PDF statement
  - Auto-detect bank
  - Extract transactions

POST /api/statements/analyze
  - Generate AI insights from statement
  - Pattern detection
  - Risk assessment

GET /api/statements/{user_id}
  - Retrieve user's parsed statements
```

#### **PDF Parsing Flow**:
1. Upload PDF (optional password)
2. Detect bank from header/logo
3. Extract transaction table
4. Parse amounts, dates, descriptions
5. Calculate running balance
6. Store in Supabase
7. Generate Groq AI insights
8. Return transactions + insights

---

## 🎨 3. FRONTEND IMPLEMENTATION

### **Current Files**
- **index.html** - Splash/landing page
- **dashboard.html** - Main analysis dashboard
- **assets/app.js** - JavaScript logic (500+ lines)
- **assets/style.css** - Styling (Premium white & green theme)
- **manifest.json** - PWA config
- **sw.js** - Service worker

### **Theme Implementation** (Cleo-Mode)
**Current**: Warm/Earthy variant
- Background: `#f8f4ee` (warm beige)
- Primary: `#47201c` (dark brown)
- Accent: `#e98e4a` (warm orange)
- Default: Green variant with `#00d084` primary

### **UI Components Built**

#### **1. Input Section**
- **SMS Tab**:
  - Textarea with demo placeholder
  - "Analyze My Finances" button
  - "Load Demo Data" button
- **CSV Tab**:
  - Drag-and-drop upload area
  - File browser fallback
  - "Analyze Statement" button
  - "Load Demo CSV" button
- CSV preview shows filename + row count

#### **2. Loading Panel**
- Animated spinner
- 4-step progress display:
  1. Reading SMS (📱)
  2. Calculating Score (🧠)
  3. Predicting Future (📈)
  4. Generating Actions (⚡)
- Steps animate sequentially (550ms each)

#### **3. Results Panel** (Shown after analysis)
- **Financial Health Score Card**:
  - Animated circular progress ring (SVG)
  - Score number (0-100) with animation
  - Label (Healthy/Moderate/Unstable/Critical)
  - Color-coded by status (green/yellow/orange/red)
  - Message explaining score

- **Days to Zero Card**:
  - Shows days remaining
  - Daily burn rate in naira
  - Urgency indicator (low/medium/high/critical)
  - Color-coded by urgency

- **Behavior Patterns Card**:
  - Lists detected patterns with severity
  - Shows pattern title + detail
  - Severity badges (low/medium/high)
  - Staggered animation entrance

- **Score Pillars Card** (Breakdown visualization):
  - 5 pillars visualized as bars:
    1. Income Stability (25 pts max)
    2. Spending Control (25 pts max)
    3. Savings Behavior (20 pts max)
    4. Bill Regularity (15 pts max)
    5. Category Diversity (15 pts max)
  - Each bar animates to target percentage
  - Shows current/max score

- **Transaction Timeline Card**:
  - Shows last 8 transactions (sorted by date)
  - Credit (green, +) / Debit (red, -) indicators
  - Amount, description, date, category
  - Total transaction count
  - Scrollable within card

#### **4. AI Actions Section**
- "Fix This" button triggers action panel
- Displays 3-5 personalized actions
- Each action shows:
  - Action number
  - Title (data-driven)
  - Detail (with calculated numbers)
  - Impact level (high/medium/low)
  - Staggered entrance animation

#### **5. Interswitch Integration Panel**
- Two action buttons:
  - "Simulate Saving ₦5,000"
  - "Simulate Bill Optimization"
- Requires Google OAuth sign-in (auth modal)
- Shows execution results

#### **6. Auth Modal**
- Title: "Sign in to execute this action"
- Explains Interswitch use
- "Sign in with Google" button
- Security note: "We never store your bank password"
- Close/Cancel button

#### **7. Toast Notifications**
- Success/error/warning messages
- Auto-dismiss
- Non-intrusive positioning

### **Frontend State Management**
```javascript
let currentResults = null;        // Latest analysis result
let csvContent = null;            // CSV file content
let activeTab = "sms";            // Current input mode
```

### **Key Functions**
- `analyzeNow()` - Trigger SMS analysis
- `analyzeCSV()` - Trigger CSV analysis
- `renderResults(data)` - Display all results
- `renderScore(s)` - Animated score card
- `renderDaysToZero(d)` - Days card with urgency
- `renderPatterns(p)` - Pattern list
- `renderPillars(pillars)` - Score breakdown bars
- `renderTimeline(txns)` - Transaction list
- `renderActions(actions)` - AI actions list
- `simulateSave()` / `simulateBill()` - Interswitch actions (auth-gated)

---

## 🔗 4. BACKEND <—> FRONTEND CONNECTIONS

### **Working Connections**
✅ **POST /api/analyze**
- Frontend: Calls on SMS submit
- Sends: Raw SMS text
- Receives: Complete analysis result
- Displays: Score, days, patterns, actions, transactions

✅ **CSV Analysis**
- Frontend: Parses CSV locally, builds SMS from transactions
- Sends: Synthetic SMS to `/api/analyze`
- Flow: CSV → parse locally → SMS format → /api/analyze

✅ **AI Actions Display**
- Backend: Generates genuine actions from data
- Frontend: Displays with animations
- Auth: requires Google sign-in for Interswitch

✅ **Demo Data**
- Frontend: Pre-loaded demo SMS & CSV
- No backend call needed for demo load
- Full analysis when "Analyze" clicked

---

### **Missing/Incomplete Connections**

⚠️ **GET /api/history/{user_id}**
- **Backend**: Fully implemented
- **Frontend**: No UI for saving/loading history
- **Missing**: Button to fetch user's history after sign-in
- **Impact**: Can't re-analyze without re-pasting SMS

⚠️ **PDF Upload**
- **Backend**: `/api/parse/csv` accepts file upload
- **Frontend**: CSV tab has file upload UI
- **Issue**: No `/api/parse/pdf` endpoint in main API
- **Note**: PDF parsing service is separate (finsight-pdf)
- **Missing**: Connection to finsight-pdf service

⚠️ **Interswitch Execution**
- **Backend**: `services/interswitch.py` has full integration
- **Frontend**: Buttons & modals built
- **Missing**: Actual execution flow / result display
- **Incomplete**: `_doSave()` and `_doBill()` in app.js are stubbed

⚠️ **User History**
- **Backend**: Saves transactions to Supabase
- **Frontend**: No "View History" button
- **Missing**: History fetch & merge with current analysis

⚠️ **Theme Switching**
- **Frontend**: CSS has dark theme variables
- **Missing**: Theme toggle UI element
- **Missing**: LocalStorage persistence

⚠️ **Error Handling**
- **Backend**: Graceful fallbacks for all services
- **Frontend**: Uses mock data if API unavailable
- **Gap**: No detailed error display to user

---

## 📚 5. SERVICES (services/ folder)

### **A. SMS Parser** (sms_parser.py)
**Owner**: TBD

**Functions**:
- `parse_sms(sms_text, bank_type)` - Parse single SMS
- `parse_multiple_sms(sms_list)` - Batch parse
- Bank-specific parsers:
  - `parse_access_bank_sms()`
  - `parse_gtbank_sms()`
  - `parse_first_bank_sms()`
  - `parse_zenith_sms()`
  - `parse_uba_sms()`

**Output Format**:
```json
{
  "bank": "gtbank",
  "amount": 1000,
  "date": "2026-03-18",
  "time": "12:00:00",
  "type": "credit",
  "description": "SALARY",
  "balance": 100000
}
```

---

### **B. CSV Parser** (csv_parser.py)
**Owner**: TBD

**Functions**:
- `parse_csv(csv_content)` - Parse CSV string
- `detect_delimiter()` - Auto-detect delimiter
- `parse_csv_row()` - Parse single row
- `categorize_transaction()` - Auto-categorize
- `calculate_balances()` - Compute running balance

**Supported Banks**: All major Nigerian banks (GTBank, Access, UBA, Zenith, FirstBank, etc.)

**Output Format**: Same as SMS parser

---

### **C. Score Engine** (score_engine.py)
**Owner**: Toby

**Functions**:

1. **`calculate_score(transactions)` - [0-100 Financial Health Score]**
   - **Pillars** (weighted):
     - Income Stability (25%): Multiple income sources
     - Spending Control (25%): Spending vs income ratio
     - Savings Behavior (20%): Savings keywords detected
     - Bill Regularity (15%): Bill payment history
     - Category Diversity (15%): Spending across categories
   - **Output Labels**:
     - 80-100: "Financially Healthy" (green)
     - 55-79: "Moderate Risk" (yellow)
     - 40-54: "Financially Unstable" (orange)
     - 0-39: "Critical" (red)

2. **`days_to_zero(transactions, current_balance)` - [Runway Prediction]**
   - Calculates daily burn rate
   - Accounts for spending volatility
   - Estimates days until balance depletion
   - Returns urgency level (low/medium/high/critical)
   - **Formula**:
     ```
     daily_burn = total_spending / active_spend_days
     days_remaining = current_balance / daily_burn
     ```

3. **`detect_patterns(transactions)` - [Behavior Pattern Detection]**
   - Post-salary spending spike
   - Weekend overspending
   - Recurring bills awareness
   - Data spending concentration
   - High-value transaction clusters

4. **`generate_actions()` - [AI Action Recommendations (Wrapper)]**
   - Calls `ai_actions.generate_genuine_actions()`
   - Returns prioritized action list

---

### **D. AI Actions** (ai_actions.py)
**Owner**: Toby

**Main Function**: `generate_genuine_actions(score_result, days_result, pattern_result, raw_transactions, user_context)`

**Data-Driven Logic**:
- Every sentence built from actual transaction numbers
- No hardcoded strings
- Actions are unique per user
- Interswitch integration data included

**Action Categories**:
1. Spending cuts (highest category reduction)
2. Data bundle optimization
3. Electricity bill automation
4. Savings lock-on-payday
5. Weekend spending caps
6. DSTV/subscription auto-pay

---

### **E. Database Layer** (db.py)
**Owner**: Backend Partner

**Supabase Tables**:
- `transactions` - All user transactions (with dedup hash)
- `financial_scores` - Daily scores per user
- `user_bank_profiles` - Bank details for Interswitch

**Functions**:
- `save_transaction(user_id, data)` - Insert with dedup
- `get_user_transactions(user_id, limit=50)` - Fetch history
- `save_score()` / `get_latest_score()` - Score management
- `delete_transaction()` / `clear_user_transactions()`

---

### **F. Interswitch Integration** (interswitch.py)
**Owner**: Pogbe

**Sandbox Environment**: All calls to `sandbox.interswitchng.com`

**Functions**:
- `get_access_token()` - OAuth2 token management
- `pay_bill(biller_code, customer_id, amount_naira, user_id)` - Execute bill payment
- `get_data_bundles(network)` - Fetch available bundles

**Supported Billers**:
- IKEDC (BIL119) - Prepaid electricity
- DSTV (BIL110) - TV subscription
- MTN (BIL124) - Airtime + Data
- Airtel (BIL125)
- Glo (BIL127)
- 9Mobile (BIL126)

---

### **G. Demo Data Seeder** (demo_seeder.py)
- Populates demo transactions
- Used for testing & presentations
- Not exposed via API

---

### **H. Other Services**
- `sme_csv_engine.py` - SME-specific CSV parsing
- `testing_integration.py` - Integration test suite

---

## 🛠️ 6. WHAT'S MISSING / NEEDS CONNECTION

### **Priority 1: Must Connect** 
1. **User History View**
   - Add "View My History" button post-login
   - Call `GET /api/history/{user_id}`
   - Merge with current analysis
   - Allow comparison over time

2. **PDF Upload**
   - Connect CSV upload to finsight-pdf service
   - Get finsight-pdf endpoint URL
   - Add async PDF parsing workflow
   - Show parsing progress

3. **Interswitch Execution**
   - Complete `_doSave()` and `_doBill()` functions
   - Call backend bill payment API
   - Show transaction reference
   - Display success/failure feedback

4. **Persistent User Session**
   - Store Google auth token
   - Persist `user_id` across sessions
   - Auto-load history on login
   - Save user preferences

### **Priority 2: Should Add**
1. **Dark Theme Toggle**
   - Implement theme switch UI
   - Persist to localStorage
   - Full dark theme in CSS (variables exist)

2. **Detailed Error Messages**
   - Show API error details to user
   - Guidance on SMS format issues
   - Bank-specific examples

3. **Transaction Editing**
   - Let users correct parsed amounts/dates
   - Re-save to DB
   - Recalculate score

4. **Multi-Account Support**
   - Analyze multiple banks together
   - Compare accounts
   - Aggregate score

5. **Export Functionality**
   - Download analysis as PDF
   - Export transactions as CSV
   - Share results via link

### **Priority 3: Nice to Have**
1. **Account Linking**
   - Connect real bank accounts
   - Auto-import statements (API)
   - Real-time alerts

2. **Goal Setting**
   - Set savings targets
   - Track progress
   - Milestone celebrations

3. **Notifications**
   - Low balance alerts
   - Unusual spending warnings
   - Bill reminders

4. **Financial Planning**
   - Budget templates
   - Category insights
   - Trend analysis

---

## 📦 SUMMARY TABLE

| Component | Status | Owner | Notes |
|-----------|--------|-------|-------|
| SMS Parsing | ✅ Complete | - | 5 banks supported |
| CSV Parsing | ✅ Complete | - | 13 banks supported |
| Score Engine | ✅ Complete | Toby | 5-pillar model |
| Days-to-Zero | ✅ Complete | Toby | Volatility-aware |
| Pattern Detection | ✅ Complete | Toby | 5 core patterns |
| AI Actions | ✅ Complete | Toby | Data-driven, zero hardcoding |
| PDF Parser | ✅ Complete | Margaret | Encrypted PDF support |
| Interswitch Integration | ✅ Complete | Pogbe | Sandbox tested |
| Supabase DB | ✅ Complete | - | Transactions, scores |
| Frontend Dashboard | ✅ Built | - | All UI components exist |
| Frontend Results | ✅ Built | - | Score, days, patterns, actions |
| SMS Input | ✅ Built | - | Tab + demo |
| CSV Input | ✅ Built | - | Drag-drop upload |
| Auth Modal | ✅ Built | - | Google OAuth gated |
| Interswitch UI | ⚠️ Stubbed | - | Buttons exist, execution missing |
| History View | ❌ Missing | - | Endpoint built, UI missing |
| PDF Upload | ⚠️ Partial | - | CSV works, PDF API connection missing |
| Dark Theme | ⚠️ CSS Only | - | Variables exist, toggle missing |
| Error Handling | ⚠️ Partial | - | Mock fallback works, UX could improve |

---

## 🎯 NEXT STEPS RECOMMENDED

1. **Complete Interswitch Flow** (1 day)
   - Wire `_doSave()` and `_doBill()` 
   - Test sandbox transactions
   - Display reference numbers

2. **Add History View** (1 day)
   - Post-login history button
   - Merge with current analysis
   - Show date selector

3. **Connect PDF Service** (1-2 days)
   - Get finsight-pdf deployment URL
   - Add PDF endpoint to main API
   - Wire frontend upload

4. **Polish User Experience** (2-3 days)
   - Better error messages
   - Dark theme toggle
   - Loading states refinement
   - Toast feedback

5. **Production Deployment** (1 day)
   - Environment variables hardening
   - Rate limiting
   - CORS tightening
   - Authentication enforcement
