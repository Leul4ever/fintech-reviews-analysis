# Task 2: Theme Grouping Logic Documentation

## Overview
Themes are identified by matching review text against predefined keyword patterns. Each theme represents a category of user feedback that can help banks understand satisfaction drivers and pain points.

## Theme Categories

### 1. Account Access Issues
**Keywords:** login, pin, otp, password, credential, account, activation, access
**Purpose:** Captures reviews about authentication problems, login failures, PIN/OTP issues, and account access difficulties.

### 2. Transaction Performance  
**Keywords:** transfer, pending, delay, slow, failed, processing, transaction, speed
**Purpose:** Identifies feedback about transaction speed, failures, delays, and processing issues.

### 3. User Interface & Experience
**Keywords:** ui, interface, design, navigation, layout, experience, user-friendly
**Purpose:** Captures feedback about app design, usability, and user experience.

### 4. Reliability & Stability
**Keywords:** crash, error, bug, freeze, lag, issue, stability, reliable
**Purpose:** Identifies technical problems, app crashes, bugs, and stability issues.

### 5. Customer Support & Communication
**Keywords:** support, service, help, respond, call, branch, customer, care
**Purpose:** Captures feedback about customer service quality and communication.

### 6. Feature Requests
**Keywords:** feature, add, need, would like, option, card, request, suggestion
**Purpose:** Identifies user requests for new features or improvements.

## Detection Method

1. **Text Preprocessing:** Reviews are lowercased and cleaned (punctuation removed, whitespace normalized).
2. **Keyword Matching:** Each review is checked against all theme keyword lists.
3. **Multi-Theme Assignment:** A review can match multiple themes if it contains keywords from different categories.
4. **Default Theme:** Reviews that don't match any specific theme are assigned "Other Feedback".

## Implementation Details

- **TF-IDF Extraction:** Top keywords per bank are extracted using TF-IDF (max_features=1000, ngram_range=(1,2)).
- **Stop-word Removal:** English stop words are filtered using scikit-learn's default stop word list.
- **Theme Matching:** Direct substring matching in cleaned review text (case-insensitive).

## Notes

- The "Other Feedback" theme typically has high coverage (90%+) as it serves as a catch-all for reviews that don't match specific patterns.
- Reviews can have multiple themes (e.g., a review mentioning both "crash" and "slow transfer" will match both "Reliability & Stability" and "Transaction Performance").
- Theme keywords are designed to be broad enough to capture related concepts while specific enough to avoid false positives.

