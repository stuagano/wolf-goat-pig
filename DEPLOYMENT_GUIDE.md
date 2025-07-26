# Wolf Goat Pig Deployment Guide

This guide covers deploying the Wolf Goat Pig application to both Render (backend) and Vercel (frontend).

## 🚀 Quick Deploy

### Option 1: Render + Vercel (Recommended)
- **Backend**: Deploy to Render (PostgreSQL database included)
- **Frontend**: Deploy to Vercel (optimal React hosting)

### Option 2: All on Render
- **Backend + Frontend**: Deploy both to Render

## 📋 Prerequisites

1. **GitHub Account** with your forked repository
2. **Render Account** (free tier available)
3. **Vercel Account** (free tier available)

## 🔧 Backend Deployment (Render)

### 1. Create Render Account
- Go to [render.com](https://render.com)
- Sign up with GitHub

### 2. Deploy Database
1. Click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `wolf-goat-pig-db`
   - **Database**: `wolf_goat_pig`
   - **User**: `wolf_goat_pig_user`
   - **Region**: Choose closest to you
   - **Plan**: Free
3. Click **"Create Database"**
4. **Save the connection details** (you'll need the DATABASE_URL)

### 3. Deploy Backend API
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `wolf-goat-pig-api`
   - **Root Directory**: `backend`
   - **Environment**: Python
   - **Build Command**: 
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     python -c "from app.database import init_db; init_db()" && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
     ```
4. **Environment Variables**:
   - `DATABASE_URL`: (Link to your database)
   - `ENVIRONMENT`: `production`
   - `FRONTEND_URL`: `https://your-frontend-url.vercel.app`
5. Click **"Create Web Service"**

### 4. Health Check
- Render will automatically check `/health` endpoint
- Deployment successful when health check passes

## 🌐 Frontend Deployment (Vercel)

### 1. Create Vercel Account
- Go to [vercel.com](https://vercel.com)
- Sign up with GitHub

### 2. Deploy Frontend
1. Click **"New Project"**
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
4. **Environment Variables**:
   - `REACT_APP_API_URL`: `https://your-backend-url.onrender.com`
   - `NODE_ENV`: `production`
5. Click **"Deploy"**

### 3. Configure Custom Domain (Optional)
1. Go to **Project Settings** → **Domains**
2. Add your custom domain
3. Follow DNS configuration instructions

## 🔄 Alternative: All on Render

If you prefer to deploy everything on Render:

### 1. Deploy Backend (Same as above)

### 2. Deploy Frontend to Render
1. Click **"New +"** → **"Static Site"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `wolf-goat-pig-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm ci --only=production && npm run build`
   - **Publish Directory**: `build`
4. **Environment Variables**:
   - `REACT_APP_API_URL`: `https://your-backend-url.onrender.com`
   - `NODE_ENV`: `production`
5. Click **"Create Static Site"**

## 🔐 Environment Variables Reference

### Backend (Render)
```bash
DATABASE_URL=postgresql://...  # Provided by Render database
ENVIRONMENT=production
FRONTEND_URL=https://your-frontend-url.vercel.app
USGA_API_KEY=optional_api_key  # For course import
GHIN_API_KEY=optional_api_key  # For course import
GOLF_NOW_API_KEY=optional_api_key  # For course import
THEGRINT_API_KEY=optional_api_key  # For course import
```

### Frontend (Vercel)
```bash
REACT_APP_API_URL=https://your-backend-url.onrender.com
NODE_ENV=production
```

## 🔍 Troubleshooting

### Common Backend Issues

#### 1. Import Errors
```
ModuleNotFoundError: No module named 'backend'
```
**Solution**: Ensure all imports use relative paths (fixed in codebase)

#### 2. Database Connection Issues
```
could not translate host name
```
**Solutions**:
- Verify DATABASE_URL is correctly set
- Check database service is running
- Ensure database and web service are in same region

#### 3. Health Check Failures
```
Health check failed
```
**Solutions**:
- Check logs for startup errors
- Verify `/health` endpoint works locally
- Ensure database initialization completes

### Common Frontend Issues

#### 1. API Connection Issues
```
Network Error / CORS Error
```
**Solutions**:
- Verify REACT_APP_API_URL is correct
- Check backend CORS configuration
- Ensure backend is deployed and running

#### 2. Build Failures
```
Build failed
```
**Solutions**:
- Check for TypeScript/syntax errors
- Verify all dependencies are in package.json
- Check build logs for specific errors

#### 3. Routing Issues (Vercel)
```
404 on page refresh
```
**Solution**: Ensure vercel.json has correct routing rules (included in repo)

## 📊 Monitoring & Logs

### Render
- **Logs**: Go to service → **Logs** tab
- **Metrics**: Monitor CPU, memory, response times
- **Health**: Check health status and uptime

### Vercel
- **Functions**: Monitor function execution
- **Analytics**: View traffic and performance
- **Build Logs**: Check deployment logs

## 🔄 Auto-Deployment

Both platforms support automatic deployment:
- **Render**: Redeploys on git push to main branch
- **Vercel**: Redeploys on git push to main branch

Configure in project settings if needed.

## 🎯 Performance Optimization

### Backend (Render)
- Use connection pooling (configured)
- Enable caching headers
- Monitor database performance
- Consider upgrading to paid plan for better performance

### Frontend (Vercel)
- Assets are automatically cached
- Images optimized automatically
- CDN distribution included
- Consider Vercel Pro for advanced features

## 🔒 Security Checklist

### Backend
- ✅ Database credentials secure
- ✅ CORS properly configured
- ✅ Environment variables set
- ✅ Health checks enabled
- ✅ Error handling in place

### Frontend
- ✅ API URL configured
- ✅ No sensitive data in client
- ✅ Security headers configured
- ✅ HTTPS enabled

## 🆘 Support

### Getting Help
1. **Check logs** first for error details
2. **Render Support**: [render.com/docs](https://render.com/docs)
3. **Vercel Support**: [vercel.com/docs](https://vercel.com/docs)
4. **GitHub Issues**: Create issue in repository

### Useful Commands

#### Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm start
```

#### Database Reset (if needed)
```bash
# On Render, go to database → Settings → Reset Database
```

## 🚀 Go Live

1. ✅ Backend deployed to Render
2. ✅ Database connected and initialized
3. ✅ Frontend deployed to Vercel
4. ✅ Environment variables configured
5. ✅ Health checks passing
6. ✅ CORS working between frontend/backend
7. ✅ Test full application flow

Your Wolf Goat Pig application is now live! 🎉

---

**Need help?** Check the troubleshooting section or create an issue in the GitHub repository.