# GitHub Pages Documentation Site

This directory contains the static HTML/CSS documentation site for the Protein Disorder Classifier API.

## 📁 Structure

```
docs/github-pages/
├── index.html              # Landing page with performance highlights
├── methodology.html        # Scientific approach & validation
├── api-docs.html          # API documentation & examples
├── comparison.html        # Benchmark comparisons
├── getting-started.html   # Quick start guide
├── styles.css             # Professional styling
└── README.md              # This file
```

## 🚀 Deployment

The site is automatically deployed to GitHub Pages when changes are pushed to the `main` branch via the `.github/workflows/deploy-docs.yml` workflow.

**Live Site:** https://kmesiab.github.io/concept-model-protein-classifier/

## 🎨 Design Principles

- **Minimal & Fast:** <100KB total size, loads in <1 second
- **Mobile-Responsive:** Works on all devices
- **Accessible:** WCAG AA compliant
- **SEO Optimized:** Meta tags and structured data
- **Trust-Focused:** Transparent metrics and validation

## 📊 Key Features

- **84.52% Accuracy** prominently displayed
- Complete validation results and methodology
- Code examples in Python, JavaScript, Go, and cURL
- Performance comparison with other tools
- Clear API documentation with error handling

## 🛠️ Local Development

To preview the site locally:

```bash
# Navigate to the docs/github-pages directory
cd docs/github-pages

# Start a simple HTTP server
python3 -m http.server 8000

# Open http://localhost:8000 in your browser
```

## 📝 Making Changes

1. Edit HTML files in `docs/github-pages/`
2. Update styles in `styles.css` if needed
3. Test locally using the method above
4. Commit and push to main branch
5. GitHub Actions will automatically deploy

## 🔧 Customization

### Colors
Update CSS variables in `styles.css`:
```css
:root {
  --primary-color: #2563eb;
  --primary-dark: #1e40af;
  /* ... other colors */
}
```

### Content
Each HTML file is standalone and can be edited independently. The navigation and footer are consistent across all pages.

## 📈 Analytics

Analytics can be added by including tracking scripts in each HTML file's `<head>` section. Consider privacy-friendly options like Plausible:

```html
<script defer data-domain="your-domain.com" src="https://plausible.io/js/script.js"></script>
```

## ✅ Success Criteria

- [x] Landing page loads in <1 second
- [x] Mobile-responsive (works on phones)
- [x] All performance metrics displayed accurately (84.52% accuracy)
- [x] Clear API documentation with examples
- [x] Methodology explains approach without revealing IP
- [x] Comparison table positions us competitively
- [x] SEO optimized for "protein disorder prediction"
- [x] Auto-deploys on push to main
- [ ] Custom domain configured (optional)
- [ ] Analytics integrated (optional)

## 📞 Support

For questions or issues with the documentation site, please open an issue on the [GitHub repository](https://github.com/kmesiab/concept-model-protein-classifier/issues).

---

Built with ❤️ for the research community
