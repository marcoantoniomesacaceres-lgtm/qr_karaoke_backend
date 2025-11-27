const fs = require('fs');
const path = require('path');
const vm = require('vm');

function checkFile(filePath) {
    let code = fs.readFileSync(filePath, 'utf8');

    if (filePath.endsWith('.html')) {
        // Extract script content
        const scriptRegex = /<script>([\s\S]*?)<\/script>/g;
        let match;
        let scriptCount = 0;
        while ((match = scriptRegex.exec(code)) !== null) {
            scriptCount++;
            const scriptContent = match[1];
            try {
                new vm.Script(scriptContent);
                console.log(`✅ ${filePath} (Script ${scriptCount}): OK`);
            } catch (e) {
                console.error(`❌ ${filePath} (Script ${scriptCount}): Syntax Error: ${e.message}`);
            }
        }
    } else if (filePath.endsWith('.js')) {
        try {
            new vm.Script(code);
            console.log(`✅ ${filePath}: OK`);
        } catch (e) {
            console.error(`❌ ${filePath}: Syntax Error: ${e.message}`);
        }
    }
}

function walkDir(dir) {
    const files = fs.readdirSync(dir);
    files.forEach(file => {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        if (stat.isDirectory()) {
            walkDir(filePath);
        } else if (filePath.endsWith('.js') || filePath.endsWith('.html')) {
            checkFile(filePath);
        }
    });
}

walkDir('./static');
