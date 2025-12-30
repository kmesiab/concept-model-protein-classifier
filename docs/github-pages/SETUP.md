# GitHub Pages Setup Instructions

## ✅ What's Already Done

The complete GitHub Pages documentation site has been created and is ready to deploy. All files are in the `docs/github-pages/` directory:

- ✅ 5 HTML pages (landing, methodology, API docs, comparison, getting started)
- ✅ Professional CSS styling (mobile-responsive, accessible)
- ✅ GitHub Actions deployment workflow
- ✅ SEO optimization (meta tags, structured data)
- ✅ Total size: 85KB (under 100KB target)

## 📋 Required Steps to Enable GitHub Pages

### Step 1: Enable GitHub Pages in Repository Settings

1. Go to your repository: https://github.com/kmesiab/concept-model-protein-classifier
2. Click **Settings** (tab at the top)
3. Click **Pages** (in the left sidebar)
4. Under "Build and deployment":
   - **Source:** Deploy from a branch
   - **Branch:** Select `gh-pages` (will be created automatically on first workflow run)
   - **Folder:** Select `/ (root)`
5. Click **Save**

### Step 2: Trigger the First Deployment

The workflow is configured to deploy automatically when changes are pushed to `main` that affect `docs/github-pages/**` files.

**Option A: Merge this PR**
- Merging this PR will automatically trigger the deployment workflow
- The site will be live within 1-2 minutes

**Option B: Manual Trigger**
1. Go to **Actions** tab
2. Select "Deploy Documentation to GitHub Pages"
3. Click "Run workflow"
4. Select branch (main or your PR branch)
5. Click "Run workflow"

### Step 3: Verify Deployment

1. After the workflow completes (1-2 minutes), go to **Settings → Pages**
2. You should see: "Your site is live at https://kmesiab.github.io/concept-model-protein-classifier/"
3. Click the link to visit your new documentation site!

## 🎯 Optional Enhancements

### Custom Domain (Optional)

If you want to use a custom domain like `protein-classifier.com`:

1. **Add CNAME file:**
   ```bash
   echo "protein-classifier.com" > docs/github-pages/CNAME
   git add docs/github-pages/CNAME
   git commit -m "Add custom domain"
   git push
   ```

2. **Configure DNS:**
   - Add a CNAME record pointing to: `kmesiab.github.io`
   - Or add A records pointing to GitHub Pages IPs:
     - 185.199.108.153
     - 185.199.109.153
     - 185.199.110.153
     - 185.199.111.153

3. **Enable in Settings:**
   - Go to Settings → Pages
   - Enter your custom domain
   - Check "Enforce HTTPS" (recommended)

### Analytics Integration (Optional)

To track site usage, add analytics to each HTML file:

**Option A: Plausible (Privacy-Friendly)**
```html
<!-- Add before </head> in each HTML file -->
<script defer data-domain="your-domain.com" src="https://plausible.io/js/script.js"></script>
```

**Option B: Google Analytics**
```html
<!-- Add before </head> in each HTML file -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### SEO Optimization (Optional)

1. **Submit to Google Search Console:**
   - Verify your site at https://search.google.com/search-console
   - Submit your sitemap (create one or use a generator)

2. **Create sitemap.xml:**
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
     <url>
       <loc>https://kmesiab.github.io/concept-model-protein-classifier/</loc>
       <priority>1.0</priority>
     </url>
     <url>
       <loc>https://kmesiab.github.io/concept-model-protein-classifier/methodology.html</loc>
       <priority>0.8</priority>
     </url>
     <!-- Add other pages -->
   </urlset>
   ```

## 🐛 Troubleshooting

### Workflow Not Running?

**Check workflow permissions:**
1. Settings → Actions → General
2. Scroll to "Workflow permissions"
3. Select "Read and write permissions"
4. Check "Allow GitHub Actions to create and approve pull requests"
5. Click Save

### 404 Error on Site?

**Wait a few minutes** - First deployment can take 5-10 minutes.

**Check deployment status:**
1. Go to Actions tab
2. Look for "Deploy Documentation to GitHub Pages"
3. Check if it completed successfully
4. If failed, click on it to see error logs

### Site Not Updating?

**Clear GitHub Pages cache:**
1. Make a trivial change to any HTML file
2. Commit and push
3. Wait 1-2 minutes for redeployment

## 📊 Monitoring

### Check Site Status

- **Deployment Status:** Actions tab → "Deploy Documentation to GitHub Pages"
- **Site URL:** Settings → Pages (shows current deployment URL)
- **Build Logs:** Click on any workflow run in Actions tab

### Traffic Analysis (After Adding Analytics)

- Plausible: https://plausible.io/your-domain.com
- Google Analytics: https://analytics.google.com

## 🔒 Security

### Enable HTTPS (Recommended)

1. Settings → Pages
2. Check "Enforce HTTPS"
3. GitHub will automatically provision an SSL certificate

### Dependabot (Optional)

GitHub Actions versions will be kept up to date automatically if you enable Dependabot:
1. Settings → Security → Code security and analysis
2. Enable "Dependabot version updates"

## 📞 Support

If you encounter issues:

1. **Check the workflow logs:** Actions tab → failed workflow → click on job
2. **Verify file permissions:** Ensure all HTML/CSS files are readable
3. **Test locally:** Run `python3 -m http.server 8080` in `docs/github-pages/`
4. **Open an issue:** If problems persist, open a GitHub issue with error details

---

**Expected Result:** After following these steps, your documentation site will be live at:
- **Default URL:** https://kmesiab.github.io/concept-model-protein-classifier/
- **Custom URL:** https://your-custom-domain.com (if configured)

Showcasing your 84.52% accurate protein disorder classifier to the world! 🧬✨
