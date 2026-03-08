const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

(async () => {
    console.log("🚀 Starting Enterprise Healthcare RAG Demo Automation...");

    // Launch browser
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--window-size=1440,900']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });

    try {
        console.log("1️⃣ Navigating to Local RAG Interface...");
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });
        await page.screenshot({ path: '01_Initial_Interface.png' });
        console.log("   📸 Saved 01_Initial_Interface.png");

        console.log("2️⃣ Submitting vague medical query...");
        await page.focus('textarea');
        await page.keyboard.type('show me lab results');
        await page.keyboard.press('Enter');

        // The Zustand store has a 1.5s simulated network delay
        await delay(2000);
        await page.screenshot({ path: '02_Clarification_Requested.png' });
        console.log("   📸 Saved 02_Clarification_Requested.png (Shows dynamic inline buttons)");

        console.log("3️⃣ Selecting Patient context for clarification...");
        // Find and click the button containing "PATTERSON" (Case insensitive for new uppercase design)
        const clicked = await page.evaluate(() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const pattersonBtn = buttons.find(b => b.textContent && b.textContent.toUpperCase().includes('PATTERSON'));
            if (pattersonBtn) {
                pattersonBtn.click();
                return true;
            }
            return false;
        });

        if (!clicked) {
            console.log("   ❌ Could not find the clarification button!");
        }

        // Wait for system to switch Focus Drawer and stream response
        await delay(2500);
        await page.screenshot({ path: '03_RBAC_Inline_Masking.png' });
        console.log("   📸 Saved 03_RBAC_Inline_Masking.png (Shows active context drawer & redacted PHI)");

        console.log("4️⃣ Querying standard clinical protocol...");
        await page.focus('textarea');
        await page.keyboard.type('what is the heparin dosage?');
        await page.keyboard.press('Enter');

        await delay(2500);
        await page.screenshot({ path: '04_Standard_Retrieval.png' });
        console.log("   📸 Saved 04_Standard_Retrieval.png (Shows High Confidence protocol source)");

        console.log("5️⃣ Toggling Enterprise Layout (80/20 -> 70/30)...");
        // Wait just a moment to ensure UI is interactive after rapid chat sequences
        await delay(1000);

        try {
            // Wait for any button within the header string
            const toggled = await page.evaluate(() => {
                const header = document.querySelector('header');
                if (!header) return false;

                const buttons = Array.from(header.querySelectorAll('button'));
                // The toggle button is the only button in the header
                if (buttons.length > 0) {
                    buttons[0].click();
                    return true;
                }
                return false;
            });

            if (toggled) {
                console.log("   ✅ Layout Toggle clicked successfully");
            } else {
                console.log("   ❌ Could not click the Layout Toggle button in Header!");
            }

        } catch (err) {
            console.log("   ❌ Error during layout toggle!", err.message);
        }

        await delay(1500); // Wait for transition animation to complete
        await page.screenshot({ path: '05_Layout_Toggle.png' });
        console.log("   📸 Saved 05_Layout_Toggle.png (Shows Layout Flexibility)");

        console.log("\n✅ Demo finished successfully! All screenshots saved to ./demo-automation/");

    } catch (e) {
        console.error("Demo failed:", e);
    } finally {
        await browser.close();
    }
})();
