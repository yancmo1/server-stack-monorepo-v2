# QSL Card Creator - Email Functionality Guide

## Overview
The QSL Card Creator now includes comprehensive email functionality that allows you to send QSL confirmations, requests, and thank you messages directly from the application.

## Features

### 📧 Email Templates
Three pre-configured email templates are available:
- **QSL Confirmation**: For confirming a QSO contact
- **QSL Request**: For requesting a QSL card from another operator
- **TNX QSL**: For thanking someone who sent you a QSL card

### 🔍 Email Address Lookup
- Integrated HAMQTH.com lookup for finding email addresses
- Automatic email address detection from QSO data
- Manual email address entry option

### 📝 Email Composition
- Template-based email generation with QSO data auto-population
- Editable subject lines and message bodies
- Professional formatting with operator information

### 📤 Email Sending Options
- **Gmail Web Interface**: Opens Gmail in your browser with pre-filled content
- **System Email Client**: Opens your default email application with the message

## How to Use

### Step 1: Select a QSO
1. Load your ADIF database using the "Browse" button
2. Select a QSO from the list that you want to send an email about

### Step 2: Generate QSL Card (Optional)
1. Click "Generate QSL" to create a PDF QSL card
2. The card will be available for attachment in the email

### Step 3: Send Email
1. Click the "Send Email" button
2. The email dialog will open with the following options:

#### Email Dialog Options:
- **To**: Email address (auto-filled if available in QSO data)
- **Template**: Choose from QSL Confirmation, QSL Request, or TNX QSL
- **Subject**: Editable subject line (auto-generated from template)
- **Message**: Editable message body (auto-generated from template)

#### Available Actions:
- **Lookup Email**: Opens HAMQTH.com to search for the station's email
- **Send with Gmail**: Opens Gmail web interface with pre-filled email
- **Send with Email App**: Opens your system's default email client
- **Cancel**: Close the dialog without sending

### Step 4: Complete the Email
- Review and edit the message content as needed
- Attach the QSL card PDF if desired (manual process in your email client)
- Send the email

## Email Template Details

### QSL Confirmation Template
```
Subject: QSL Confirmation - [THEIR_CALL] via [YOUR_CALL]

Dear [NAME],

Thank you for our QSO on [DATE] at [TIME] UTC.

QSO Details:
- Frequency: [FREQUENCY] MHz
- Mode: [MODE]
- Signal Reports: [RST_SENT]/[RST_RECEIVED]

73 and hope to work you again soon!

de [YOUR_CALL]
[YOUR_NAME]
```

### QSL Request Template
```
Subject: QSL Request - [THEIR_CALL] worked by [YOUR_CALL]

Dear [NAME],

I hope this message finds you well. I worked your station on [DATE] and would appreciate a QSL card if possible.

QSO Details:
- Date: [DATE]
- Time: [TIME] UTC
- Frequency: [FREQUENCY] MHz
- Mode: [MODE]
- Signal Reports: [RST_SENT]/[RST_RECEIVED]

Please let me know if you need any additional information for your QSL card.

73 de [YOUR_CALL]
[YOUR_NAME]
```

### TNX QSL Template
```
Subject: TNX for QSL - [THEIR_CALL] via [YOUR_CALL]

Dear [NAME],

Thank you very much for your QSL card! I received it today and it's a beautiful card.

Our QSO details:
- Date: [DATE]
- Time: [TIME] UTC
- Frequency: [FREQUENCY] MHz
- Mode: [MODE]

I really appreciate you taking the time to QSL. QSL cards like yours make this hobby even more enjoyable!

73 and hope to work you again soon!

de [YOUR_CALL]
[YOUR_NAME]
```

## Technical Notes

### Email Address Sources
The application looks for email addresses in this order:
1. Email field in the QSO data
2. Email field in ADIF import data
3. Manual entry in the email dialog

### Browser Compatibility
- Gmail web interface works with all modern browsers
- Requires you to be logged into Gmail in your default browser

### Email Client Compatibility
- Works with any email client configured as your system default
- Tested with Mail.app (macOS), Outlook, Thunderbird

### Data Privacy
- No email data is stored or transmitted by the application
- All email composition happens locally on your computer
- HAMQTH lookup opens their website directly (external service)

## Troubleshooting

### Email Dialog Doesn't Open
- Ensure you have selected a QSO from the list
- Check that the QSO data contains valid information

### Gmail Doesn't Open
- Ensure you have a default browser set
- Check that you're logged into Gmail in your browser
- Some browsers may block popup windows - allow popups for the application

### Email Client Doesn't Open
- Ensure you have a default email client configured in your system
- Check your system's email client settings

### Missing QSO Information
- Check that your ADIF file contains complete QSO data
- Some fields may show as "Unknown" if not present in the original data

## Future Enhancements

Potential future improvements could include:
- Direct email sending (SMTP) without external clients
- Automatic QSL card PDF attachment
- Email templates customization
- Email address database integration
- Bulk email operations for multiple QSOs

---

*This functionality was integrated into QSL Card Creator v2 Enhanced - January 2024*
