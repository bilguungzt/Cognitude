# Enhanced Frontend - Quick Start Guide

## 🚀 Getting Started

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

Visit `http://localhost:5173` (or the port shown in your terminal)

### Build for Production

```bash
npm run build
npm run preview
```

## 🎯 Quick Tour

### 1. Login/Register Page (`/login`)

**Features:**

- Tab toggle between Sign In and Register
- API key visibility toggle
- Form validation
- Success/error messages
- Animated entrance

**Try it:**

1. Click "Register" tab
2. Enter organization name
3. Click "Create Account"
4. Save the API key shown
5. Use it to sign in

### 2. Enhanced Dashboard (`/dashboard`)

**Features:**

- Statistics cards showing total models, drift status
- Search bar to filter models
- Filter dropdown (All, With Drift, No Drift, Not Configured)
- Grid/List view toggle
- Auto-refresh every 30 seconds
- Manual refresh button

**Try it:**

1. Register a new model using the "Register Model" button
2. Use the search bar to find models by name
3. Toggle between Grid and List views
4. Click on a model card to view details
5. Watch for auto-refresh (last updated time changes)

### 3. Cost Dashboard (`/cost`)

**Features:**

- Quick date range buttons (7/30/90 days)
- Custom date picker
- Statistics cards with trends
- Beautiful area chart for costs
- Bar chart for requests
- Export to CSV button
- Detailed usage table

**Try it:**

1. Click "Last 7 Days" to see recent data
2. Try different date ranges
3. Click "Export CSV" to download data
4. Hover over charts to see details
5. Use refresh button to update data

## 🎨 Design System

### Colors

```tsx
// Buttons
<button className="btn-primary">Primary Action</button>
<button className="btn-secondary">Secondary Action</button>
<button className="btn-danger">Delete</button>
<button className="btn-ghost">Subtle Action</button>

// Badges
<span className="badge-success">Success</span>
<span className="badge-error">Error</span>
<span className="badge-warning">Warning</span>
<span className="badge-info">Info</span>

// Alerts
<div className="alert-success">Success message</div>
<div className="alert-error">Error message</div>
```

### Components

```tsx
// Layout wrapper
import Layout from "../components/Layout";

<Layout title="Page Title">
  <div className="max-w-7xl mx-auto px-4 py-8">{/* Content */}</div>
</Layout>;

// Toast notifications
import { useToast } from "../components/ToastContainer";
const { showToast } = useToast();
showToast("Success!", "success");
showToast("Error!", "error");

// Modal
import Modal from "../components/Modal";
<Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title="Title">
  Content
</Modal>;

// Empty State
import EmptyState from "../components/EmptyState";
<EmptyState
  icon={Package}
  title="No items"
  description="Get started by adding your first item"
  action={{ label: "Add Item", onClick: handleAdd }}
/>;

// Loading
import LoadingSpinner from "../components/LoadingSpinner";
<LoadingSpinner text="Loading..." />;

// Skeleton
import { SkeletonCard } from "../components/Skeleton";
<SkeletonCard />;
```

## 📱 Responsive Breakpoints

- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

All pages automatically adapt to screen size!

## 🎭 Testing Checklist

### Desktop

- ✅ Dashboard search and filter
- ✅ Grid/List view toggle
- ✅ Model cards clickable
- ✅ Statistics cards display correctly
- ✅ Cost charts render properly
- ✅ Date picker works
- ✅ CSV export downloads

### Mobile

- ✅ Mobile menu opens/closes
- ✅ All buttons are tappable (44x44px minimum)
- ✅ Forms are usable
- ✅ Charts are scrollable/responsive
- ✅ Cards stack vertically
- ✅ No horizontal scroll

### Functionality

- ✅ Auto-refresh updates data
- ✅ Manual refresh works
- ✅ Toast notifications appear/dismiss
- ✅ Modal opens/closes (ESC key)
- ✅ Search filters results in real-time
- ✅ Empty states show when no data
- ✅ Loading spinners appear during API calls

## 🔧 Common Customizations

### Change Brand Colors

Edit `tailwind.config.js`:

```js
theme: {
  extend: {
    colors: {
      primary: {
        500: '#YOUR_COLOR',
        600: '#YOUR_DARKER_COLOR',
        // ...
      }
    }
  }
}
```

### Add New Pages

1. Create page in `src/pages/MyPage.tsx`
2. Wrap with Layout component
3. Add route in `App.tsx`:

```tsx
<Route
  path="/mypage"
  element={
    <ProtectedRoute>
      <MyPage />
    </ProtectedRoute>
  }
/>
```

4. Layout component will automatically add it to navigation

### Customize Auto-Refresh Interval

In `DashboardPageEnhanced.tsx`, change:

```tsx
const interval = setInterval(() => {
  loadModels(true);
}, 30000); // Change 30000 to your desired milliseconds
```

## 🐛 Troubleshooting

### Styles not applying?

```bash
# Clear cache and rebuild
rm -rf node_modules/.vite
npm run dev
```

### TypeScript errors?

```bash
# Rebuild types
npm run build
```

### Components not found?

```bash
# Reinstall dependencies
rm -rf node_modules
npm install
```

### Port already in use?

```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
npm run dev
```

## 📚 Further Reading

- **Full Documentation**: `ENHANCED_FRONTEND_README.md`
- **Component Examples**: Each component file has inline documentation
- **Design System**: `index.css` for all utility classes
- **Tailwind Docs**: https://tailwindcss.com/docs

## 🎉 What's New vs Old Frontend

| Feature           | Old               | New                                     |
| ----------------- | ----------------- | --------------------------------------- |
| Design System     | Basic             | Extended with custom colors, animations |
| Components        | Inline in pages   | Reusable library                        |
| Navigation        | Separate per page | Unified Layout component                |
| Notifications     | Inline alerts     | Global toast system                     |
| Loading States    | Basic spinners    | Skeletons + spinners                    |
| Empty States      | Inline text       | Dedicated component                     |
| Dashboard         | Static list       | Search, filter, view modes, stats       |
| Cost Dashboard    | Basic charts      | Enhanced charts + export                |
| Login/Register    | Basic form        | Animated, validated, user-friendly      |
| Responsive Design | Basic             | Fully responsive with mobile menu       |
| Animations        | Minimal           | Smooth transitions everywhere           |

## 💡 Pro Tips

1. **Use the Layout component** for consistent navigation across new pages
2. **Use useToast hook** instead of inline error/success messages
3. **Always add loading states** for async operations
4. **Use empty states** when data is empty or not found
5. **Test mobile first** - easier to expand than shrink
6. **Follow the design system** - use existing classes before creating new ones
7. **Add hover states** - makes UI feel more interactive
8. **Use skeleton loaders** during initial page load
9. **Keep animations subtle** - they should enhance, not distract
10. **Maintain accessibility** - always include proper labels and ARIA attributes

## 🚀 Ready to Go!

Your enhanced frontend is ready. Start the dev server and explore the new features:

```bash
npm run dev
```

Happy coding! 🎨✨
