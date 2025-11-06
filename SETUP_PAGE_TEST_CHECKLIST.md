# Setup Page - Visual Test Checklist

## Test the Setup Page

**URL**: http://localhost:5173/setup

### ✅ Visual Tests

1. **Navigation**

   - [ ] Dashboard has "📖 Setup Guide" button in header
   - [ ] Clicking button navigates to `/setup`
   - [ ] Setup page has "← Back to Dashboard" button

2. **Hero Section**

   - [ ] Blue gradient hero banner
   - [ ] "Get Started in 5 Minutes" heading
   - [ ] Lightning bolt icon

3. **Quick Start Guide**

   - [ ] 3 numbered steps
   - [ ] Step 1: API key display with copy button
   - [ ] Step 2: "Go to Models Page" button
   - [ ] Step 3: Instructions for logging predictions

4. **Code Snippets**

   - [ ] 3 tabs: Python, Node.js, cURL
   - [ ] Tab switching works smoothly
   - [ ] Code has dark background with syntax highlighting
   - [ ] "Copy Code" button present
   - [ ] Installation instructions below each snippet
   - [ ] API key is pre-filled in all code examples

5. **Live Testing**

   - [ ] "Test Your Integration" section
   - [ ] Model ID input field
   - [ ] "Send Test Prediction" button
   - [ ] Button disabled when no API key or model ID
   - [ ] Success/error message shows after test

6. **Troubleshooting**

   - [ ] 4 common errors listed (403, 404, 422, Drift)
   - [ ] Each error has colored left border
   - [ ] Solutions clearly listed

7. **Best Practices**
   - [ ] Green/blue gradient background
   - [ ] 5 best practices with checkmarks
   - [ ] Easy to read

### ✅ Functional Tests

1. **Copy Functionality**

   ```
   Test Steps:
   1. Click "Copy" button next to API key
   2. Verify button shows "✓ Copied!" for 2 seconds
   3. Paste in text editor - should have your API key
   4. Click "Copy Code" button
   5. Paste - should have complete code snippet
   ```

2. **Tab Switching**

   ```
   Test Steps:
   1. Click "Python" tab - verify Python code shows
   2. Click "Node.js" tab - verify Node.js code shows
   3. Click "cURL" tab - verify cURL command shows
   4. Verify API key is consistent in all tabs
   ```

3. **Live Testing**

   ```
   Test Steps:
   1. Leave Model ID empty - button should be disabled
   2. Enter Model ID "1"
   3. Button should be enabled
   4. Click "Send Test Prediction"
   5. Should see success or error message
   ```

4. **API Key Pre-fill**
   ```
   Test Steps:
   1. Login to app (API key saved in localStorage)
   2. Navigate to /setup
   3. Verify API key shows in Step 1
   4. Verify API key is in all code snippets
   5. Logout and check - should show "No API key found"
   ```

### ✅ Responsiveness Tests

1. **Desktop (1920x1080)**

   - [ ] All content visible
   - [ ] No horizontal scroll
   - [ ] Proper spacing

2. **Tablet (768x1024)**

   - [ ] Code snippets readable
   - [ ] Buttons accessible
   - [ ] No overlapping content

3. **Mobile (375x667)**
   - [ ] Hero text readable
   - [ ] Code snippets scrollable
   - [ ] Tabs work on small screens

### ✅ Integration Tests

1. **End-to-End Flow**

   ```
   Complete User Journey:
   1. Login with test account
   2. Click "📖 Setup Guide" from dashboard
   3. Copy API key from Step 1
   4. Switch to Python tab
   5. Copy Python code
   6. Enter Model ID "1" in test section
   7. Click "Send Test Prediction"
   8. Verify success message
   9. Navigate to dashboard
   10. Verify model shows new prediction
   ```

2. **Error Handling**
   ```
   Test Error States:
   1. Enter invalid Model ID (e.g., "999")
   2. Send test prediction
   3. Should show 404 error
   4. Verify error message is user-friendly
   ```

### Expected Results

✅ **All tests pass**  
✅ **User can integrate in <5 minutes**  
✅ **Zero confusion or friction**  
✅ **Professional, polished experience**

---

## Quick Manual Test (30 seconds)

1. Open http://localhost:5173/setup
2. Look for your API key in Step 1
3. Click "Copy Code" button on Python tab
4. Paste - should see complete working code
5. **Success!** ✅

---

## Screenshot Checklist

Take screenshots of:

1. Full Setup page (hero to footer)
2. Code snippet tabs (Python, Node.js, cURL)
3. Live testing section
4. Troubleshooting section
5. Best practices section

Save to: `/docs/screenshots/setup_page/`

---

**Test Date**: November 6, 2025  
**Expected Result**: ✅ All features work perfectly  
**Actual Result**: _[To be filled after testing]_
