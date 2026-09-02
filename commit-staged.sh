#!/bin/bash
# Commit files one at a time, 20 minutes apart
# Files: individual file-by-file commits (not directories)

FILES=(
  ".env.example"
  "backend/app/config.py"
  "backend/app/services/momo_api.py"
  "frontend/index.html"
  "frontend/public/favicon.svg"
  "frontend/public/manifest.json"
  "frontend/src/App.jsx"
  "frontend/src/components/AccessibilityPanel.jsx"
  "frontend/src/components/GooglePayCheckout.jsx"
  "frontend/src/components/GoogleWalletProvisionButton.jsx"
  "frontend/src/components/LanguageSwitcher.jsx"
  "frontend/src/components/Layout.jsx"
  "frontend/src/context/AccessibilityContext.jsx"
  "frontend/src/i18n.js"
  "frontend/src/index.css"
  "frontend/src/locales/af.json"
  "frontend/src/locales/am.json"
  "frontend/src/locales/en.json"
  "frontend/src/locales/fr.json"
  "frontend/src/locales/ha.json"
  "frontend/src/locales/ig.json"
  "frontend/src/locales/nso.json"
  "frontend/src/locales/pt.json"
  "frontend/src/locales/st.json"
  "frontend/src/locales/sw.json"
  "frontend/src/locales/tn.json"
  "frontend/src/locales/ts.json"
  "frontend/src/locales/ve.json"
  "frontend/src/locales/xh.json"
  "frontend/src/locales/yo.json"
  "frontend/src/locales/zu.json"
  "frontend/src/main.jsx"
  "frontend/src/pages/Chat.jsx"
  "frontend/src/pages/Dashboard.jsx"
  "frontend/src/pages/Login.jsx"
  "frontend/src/pages/Stokvel.jsx"
  "frontend/src/pages/Transactions.jsx"
  "frontend/src/services/api.js"
  "commit-remaining.sh"
)

TOTAL=${#FILES[@]}
COUNT=1
START_TIME=$(date)

for file in "${FILES[@]}"; do
    echo "[$COUNT/$TOTAL] Committing: $file at $(date)"
    git add "$file"
    git commit -m "add $file"
    
    if [ "$COUNT" -lt "$TOTAL" ]; then
        echo "[$COUNT/$TOTAL] Waiting 20 minutes before next commit..."
        echo "    Next commit at: $(date -d '+20 minutes')"
        sleep 1200
    fi
    COUNT=$((COUNT + 1))
done

echo "All $TOTAL files committed. Started at: $START_TIME, finished at: $(date)"
