document.addEventListener('DOMContentLoaded', async () => {
    const runButton = document.getElementById('run-button');
    const repoNameHeader = document.getElementById('repo-name');
    const csvContainer = document.getElementById('csv-links-container');

    // Get the owner, repo, and token from the URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const owner = urlParams.get('owner');
    const repo = urlParams.get('repo');
    const token = urlParams.get('token');

    // Display the repo name in the header
    if (owner && repo) {
        repoNameHeader.textContent = `${owner}/${repo}`;
    }

    // A function to run the analytics
    async function runAnalytics() {
        runButton.disabled = true;
        runButton.textContent = 'Running...';
        
        try {
            const response = await fetch('/run-analytics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'owner': owner,
                    'repo': repo,
                    'token': token
                })
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                console.log("✅ Analytics script ran successfully.");
                console.log("--- Script Output ---");
                console.log(data.output);
                console.log("---------------------");
                refreshPlots();
                displayCsvLinks();
            } else {
                console.error('❌ Error running analytics: ' + data.message);
                console.error('--- Script Errors (stderr) ---');
                console.error(data.error_output);
                console.error("---------------------");
                alert('Error running analytics. Check the browser console for details.');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            alert('Failed to connect to server. Is the server running?');
        } finally {
            runButton.disabled = false;
            runButton.textContent = 'Run Analytics';
        }
    }

    function refreshPlots() {
        console.log("Attempting to refresh plots...");
        const timestamp = new Date().getTime();
        const plotImages = document.querySelectorAll('.plot-img');
        
        plotImages.forEach(img => {
            // Corrected line to replace hyphens with underscores
            const filename = img.id.replace('plot-', '').replaceAll('-', '_') + '.png';
            const newSrc = `/plots/${filename}?v=${timestamp}`;
            console.log(`Loading new image: ${newSrc}`);
            img.src = newSrc;
        });
    }

    function displayCsvLinks() {
        const csvFiles = [
            'contributors.csv',
            'prs.csv',
            'issues.csv',
            'review_events.csv',
            'review_comments.csv',
            'issue_comments.csv',
            'all_comments.csv'
        ];

        csvContainer.innerHTML = ''; // Clear previous links
        csvFiles.forEach(filename => {
            const link = document.createElement('a');
            link.href = `/csvs/${filename}`;
            link.textContent = filename;
            link.className = 'csv-link';
            link.setAttribute('download', filename); // Ensure the browser downloads the file
            csvContainer.appendChild(link);
        });
    }

    // Run analytics on initial page load if owner and repo are present
    if (owner && repo) {
        await runAnalytics();
    } else {
        // Redirect to home if no parameters are found
        console.log("No owner and repo found in URL. Redirecting to input page.");
        window.location.href = '/';
    }

    // Allow re-running analytics from the dashboard
    runButton.addEventListener('click', () => {
        runAnalytics();
    });
});
