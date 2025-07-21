# TRON Trading Dashboard

A comprehensive real-time monitoring and analytics dashboard for the TRON trading system. Built with Streamlit, this dashboard provides live insights into trading performance, system health, and risk management.

## 🚀 Features

### 📊 Overview Dashboard
- **Real-time P&L tracking** with live updates
- **Portfolio allocation** visualization
- **Active positions** monitoring
- **Recent trades** summary
- **Strategy performance** overview
- **Market sentiment** indicators

### 📈 Live Trading Monitor
- **Real-time position tracking** with current P&L
- **Trade execution timeline** and events
- **Quick action buttons** for position management
- **Risk metrics** monitoring
- **Advanced filtering** by strategy and symbol
- **Emergency controls** for risk management

### ⚙️ System Health Monitor
- **Comprehensive health checks** for all services
- **Resource usage monitoring** (CPU, Memory, Disk)
- **Service status tracking** for all components
- **Performance metrics** and trends
- **Alert management** system
- **Log analysis** and summary

### 🛡️ Risk Management
- **Real-time risk metrics** (VaR, Drawdown, Correlation)
- **Position concentration** monitoring
- **Risk alerts** and notifications
- **Portfolio risk assessment**

### 🧠 AI-Powered Insights (Coming Soon)
- **Market sentiment analysis**
- **Trade pattern recognition**
- **Strategy optimization suggestions**
- **Performance improvement recommendations**

## 🏗️ Architecture

```
dashboard/
├── app.py                          # Main Streamlit application
├── components/                     # UI components
│   ├── overview.py                # Overview page
│   ├── live_trades.py             # Live trading monitor
│   ├── system_health.py           # System health monitor
│   ├── pnl_analysis.py            # P&L analysis (coming soon)
│   ├── cognitive_insights.py      # AI insights (coming soon)
│   ├── risk_monitor.py            # Risk monitoring (coming soon)
│   └── strategy_performance.py    # Strategy analysis (coming soon)
├── data/                          # Data providers
│   ├── trade_data_provider.py     # Trading data interface
│   ├── system_data_provider.py    # System monitoring data
│   └── cognitive_data_provider.py # AI insights data
├── utils/                         # Utilities
│   ├── auth.py                    # Authentication
│   ├── config.py                  # Configuration management
│   └── notifications.py           # Alert system
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container configuration
└── README.md                      # This file
```

## 🚀 Quick Start

### Local Development

1. **Install Dependencies**
   ```bash
   cd dashboard
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   export DASHBOARD_USERNAME="admin"
   export DASHBOARD_PASSWORD="tron2024"
   export ENVIRONMENT="development"
   ```

3. **Run the Dashboard**
   ```bash
   streamlit run app.py
   ```

4. **Access the Dashboard**
   - Open your browser to `http://localhost:8501`
   - Login with username: `admin`, password: `tron2024`

### Docker Deployment

1. **Build the Image**
   ```bash
   docker build -t trading-dashboard -f dashboard/Dockerfile .
   ```

2. **Run the Container**
   ```bash
   docker run -p 8501:8501 \
     -e DASHBOARD_USERNAME=admin \
     -e DASHBOARD_PASSWORD=tron2024 \
     -e ENVIRONMENT=production \
     trading-dashboard
   ```

### Kubernetes Deployment

1. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f deployments/dashboard.yaml
   ```

2. **Access via LoadBalancer**
   ```bash
   kubectl get service dashboard-service -n gpt
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_USERNAME` | `admin` | Dashboard login username |
| `DASHBOARD_PASSWORD` | `tron2024` | Dashboard login password |
| `ENVIRONMENT` | `development` | Environment (development/production) |
| `AUTH_ENABLED` | `true` | Enable authentication |
| `REAL_TIME_UPDATES` | `true` | Enable real-time data updates |
| `AUTO_REFRESH_INTERVAL` | `30` | Auto-refresh interval in seconds |
| `FEATURE_LIVE_TRADING` | `false` | Enable live trading features |
| `ALERTS_ENABLED` | `true` | Enable alert notifications |

### Feature Flags

- `FEATURE_COGNITIVE_INSIGHTS`: Enable AI-powered insights
- `FEATURE_ADVANCED_CHARTS`: Enable advanced charting
- `FEATURE_RISK_MONITORING`: Enable risk monitoring
- `FEATURE_EXPORT_DATA`: Enable data export functionality

## 🔐 Authentication

The dashboard supports multiple user roles:

- **Admin**: Full access to all features including system controls
- **Trader**: Trading access without system administration
- **Viewer**: Read-only access to dashboard data

Default credentials:
- Admin: `admin` / `tron2024`
- Trader: `trader` / `trader123`
- Viewer: `viewer` / `viewer123`

## 📊 Data Sources

The dashboard integrates with:

- **Firestore**: Trade data and logs storage
- **Kite Connect API**: Live market data
- **Portfolio Manager**: Capital and position management
- **System Metrics**: Resource usage and health monitoring

## 🚨 Alerts and Notifications

The dashboard provides real-time alerts for:

- **Trade Events**: Entry, exit, stop-loss triggers
- **System Issues**: High resource usage, service failures
- **Risk Events**: Drawdown limits, VaR breaches
- **Performance**: Unusual trading patterns

## 📈 Monitoring and Observability

### Health Checks
- API connectivity status
- Database connection health
- System resource utilization
- Service availability

### Performance Metrics
- API response times
- Database query performance
- Trade execution latency
- System uptime

### Logging
- Structured logging with different levels
- Log aggregation and analysis
- Error tracking and alerting

## 🔄 Real-time Updates

The dashboard supports real-time updates through:
- **Auto-refresh**: Configurable refresh intervals
- **Live data streaming**: Real-time price and P&L updates
- **Event-driven updates**: Immediate updates on trade events

## 🛠️ Development

### Adding New Components

1. Create a new component in `dashboard/components/`
2. Implement the `render()` method
3. Add the component to the main app navigation
4. Update the imports in `__init__.py`

### Adding New Data Providers

1. Create a new provider in `dashboard/data/`
2. Implement required data methods
3. Add the provider to the main app initialization
4. Update component dependencies

### Customizing Styling

The dashboard uses custom CSS for styling. Modify the `_inject_custom_css()` method in `app.py` to customize the appearance.

## 🚀 Deployment

### Production Considerations

1. **Security**
   - Use strong passwords
   - Enable HTTPS in production
   - Implement proper authentication

2. **Performance**
   - Configure appropriate resource limits
   - Enable caching for better performance
   - Monitor resource usage

3. **Monitoring**
   - Set up health checks
   - Configure alerting
   - Monitor logs and metrics

### Scaling

The dashboard can be scaled by:
- Running multiple replicas in Kubernetes
- Using a load balancer for distribution
- Implementing caching layers
- Optimizing data queries

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check environment variables
   - Verify credentials
   - Check authentication configuration

2. **Data Not Loading**
   - Verify Firestore connectivity
   - Check API credentials
   - Review error logs

3. **Performance Issues**
   - Monitor resource usage
   - Check network connectivity
   - Optimize refresh intervals

### Logs and Debugging

- Dashboard logs are available in the container logs
- Enable debug mode with `DEBUG=true`
- Check system health page for detailed diagnostics

## 📝 API Integration

The dashboard integrates with the existing TRON trading system:

- **Trade Manager**: Real-time trade data
- **Portfolio Manager**: Capital and position information
- **Risk Governor**: Risk metrics and limits
- **Firestore Client**: Historical data and logs

## 🔮 Future Enhancements

### Planned Features

1. **Advanced Analytics**
   - Detailed P&L analysis
   - Strategy backtesting
   - Performance attribution

2. **AI-Powered Insights**
   - Market sentiment analysis
   - Trade pattern recognition
   - Predictive analytics

3. **Enhanced Risk Management**
   - Stress testing
   - Scenario analysis
   - Advanced risk metrics

4. **Mobile Support**
   - Responsive design
   - Mobile-optimized interface
   - Push notifications

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review system logs
- Contact the development team

## 📄 License

This dashboard is part of the TRON trading system and follows the same licensing terms.

---

**Note**: This dashboard is designed for monitoring and analysis purposes. Always verify trade actions through the primary trading system before making any decisions. 