// Simple GuardNet deployment for immediate access
package main

import (
	"fmt"
	"net/http"
	"time"

	"guardnet/dns-filter/internal/cache"
	"guardnet/dns-filter/internal/db"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
	fmt.Println("🚀 GuardNet DNS Filter - Simple Deployment")
	fmt.Println("==========================================")

	// Initialize mock services
	mockDB := db.NewMockConnection()
	mockCache := cache.NewMockRedisClient()

	// Add demo threat domains
	mockDB.AddThreatDomain("malware-test.com", "malware")
	mockDB.AddThreatDomain("phishing-example.org", "phishing")
	mockDB.AddThreatDomain("doubleclick.net", "ads")
	mockDB.AddThreatDomain("googleadservices.com", "ads")

	router := mux.NewRouter()

	// Health endpoint
	router.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{
			"status": "healthy",
			"service": "guardnet-dns-filter",
			"mode": "demo",
			"timestamp": "%s",
			"version": "1.0.0"
		}`, time.Now().Format(time.RFC3339))
	})

	// Stats endpoint
	router.HandleFunc("/stats", func(w http.ResponseWriter, r *http.Request) {
		stats, _ := mockDB.GetThreatStats(time.Now().Add(-24 * time.Hour))
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{
			"total_queries": %d,
			"blocked_queries": %d,
			"allowed_queries": %d,
			"unique_domains": %d,
			"threat_domains_loaded": 4
		}`, stats.TotalQueries, stats.BlockedQueries, stats.AllowedQueries, stats.UniqueDomains)
	})

	// Metrics endpoint
	router.Handle("/metrics", promhttp.Handler())

	// Demo dashboard
	router.HandleFunc("/demo", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		html := `<!DOCTYPE html>
<html>
<head>
    <title>GuardNet DNS Filter - Live Demo</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 3em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); transition: transform 0.3s ease; }
        .card:hover { transform: translateY(-5px); }
        .card h2 { color: #2c3e50; margin-bottom: 15px; display: flex; align-items: center; }
        .card h2::before { content: attr(data-icon); margin-right: 10px; font-size: 1.5em; }
        .status { padding: 15px; border-radius: 10px; margin: 10px 0; }
        .healthy { background: #d4edda; border-left: 4px solid #28a745; color: #155724; }
        .blocked { background: #f8d7da; border-left: 4px solid #dc3545; color: #721c24; }
        .allowed { background: #d1ecf1; border-left: 4px solid #17a2b8; color: #0c5460; }
        .endpoint { margin: 8px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        .endpoint a { color: #007bff; text-decoration: none; font-weight: 500; }
        .endpoint a:hover { text-decoration: underline; }
        .stats { font-family: 'Courier New', monospace; background: #2c3e50; color: #ecf0f1; padding: 20px; border-radius: 10px; overflow-x: auto; }
        .btn { display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 25px; transition: background 0.3s ease; margin: 5px; }
        .btn:hover { background: #0056b3; color: white; text-decoration: none; }
        .footer { text-align: center; color: white; margin-top: 30px; opacity: 0.8; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
        .live { animation: pulse 2s infinite; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ GuardNet DNS Filter</h1>
            <p>Enterprise-level internet protection through intelligent cloud-based filtering</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2 data-icon="🌐">Service Status</h2>
                <div class="status healthy">
                    <strong>✅ Status:</strong> Running (Demo Mode)<br>
                    <strong>⏰ Started:</strong> ` + time.Now().Format("15:04:05") + `<br>
                    <strong>🔧 Mode:</strong> Local Deployment<br>
                    <strong class="live">🟢 LIVE</strong>
                </div>
            </div>
            
            <div class="card">
                <h2 data-icon="🔗">API Endpoints</h2>
                <div class="endpoint">📊 <a href="/health" target="_blank">Health Check</a></div>
                <div class="endpoint">📈 <a href="/metrics" target="_blank">Prometheus Metrics</a></div>
                <div class="endpoint">📋 <a href="/stats" target="_blank">Statistics JSON</a></div>
                <div class="endpoint">🎯 <a href="/demo" target="_blank">This Dashboard</a></div>
            </div>
            
            <div class="card">
                <h2 data-icon="🛡️">Threat Detection</h2>
                <div class="allowed">
                    <strong>✅ Safe Domains:</strong><br>
                    google.com, github.com, stackoverflow.com
                </div>
                <div class="blocked">
                    <strong>🚫 Blocked Threats:</strong><br>
                    • malware-test.com (Malware)<br>
                    • phishing-example.org (Phishing)<br>
                    • doubleclick.net (Ads)<br>
                    • googleadservices.com (Ads)
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2 data-icon="📊">Live Statistics</h2>
            <div class="stats" id="stats">Loading statistics...</div>
            <div style="margin-top: 15px;">
                <a href="/stats" class="btn" target="_blank">📋 View Raw JSON</a>
                <a href="/metrics" class="btn" target="_blank">📈 Prometheus Metrics</a>
                <a href="/health" class="btn" target="_blank">❤️ Health Check</a>
            </div>
        </div>
        
        <div class="footer">
            <p>🚀 GuardNet DNS Filter v1.0.0 | 🏗️ Built with Go | 🔧 Mock Dependencies Mode</p>
            <p>Ready for Docker deployment with PostgreSQL and Redis</p>
        </div>
    </div>
    
    <script>
        function updateStats() {
            fetch('/stats')
                .then(response => response.json())
                .then(data => {
                    const statsHtml = Object.keys(data).map(key => 
                        key.padEnd(20) + ': ' + data[key]
                    ).join('\n');
                    document.getElementById('stats').textContent = statsHtml;
                })
                .catch(error => {
                    document.getElementById('stats').textContent = 'Error loading stats: ' + error;
                });
        }
        updateStats();
        setInterval(updateStats, 3000);
    </script>
</body>
</html>`
		fmt.Fprint(w, html)
	})

	// Test endpoint
	router.HandleFunc("/test", func(w http.ResponseWriter, r *http.Request) {
		domain := r.URL.Query().Get("domain")
		if domain == "" {
			domain = "google.com"
		}
		
		threatType, _ := mockDB.CheckThreatDomain(domain)
		
		w.Header().Set("Content-Type", "application/json")
		if threatType != "" {
			fmt.Fprintf(w, `{
				"domain": "%s",
				"status": "blocked",
				"threat_type": "%s",
				"timestamp": "%s"
			}`, domain, threatType, time.Now().Format(time.RFC3339))
		} else {
			fmt.Fprintf(w, `{
				"domain": "%s", 
				"status": "allowed",
				"threat_type": null,
				"timestamp": "%s"
			}`, domain, time.Now().Format(time.RFC3339))
		}
	})

	fmt.Println("\n🌐 GuardNet is now LIVE!")
	fmt.Println("=======================")
	fmt.Printf("🎯 Demo Dashboard: \033[1;34mhttp://localhost:8080/demo\033[0m\n")
	fmt.Printf("❤️  Health Check:  \033[1;32mhttp://localhost:8080/health\033[0m\n")
	fmt.Printf("📈 Metrics:        \033[1;33mhttp://localhost:8080/metrics\033[0m\n")
	fmt.Printf("📋 Statistics:     \033[1;36mhttp://localhost:8080/stats\033[0m\n")
	fmt.Printf("🧪 Test API:       \033[1;35mhttp://localhost:8080/test?domain=malware-test.com\033[0m\n")
	fmt.Println("\n🚀 Click the links above to access GuardNet!")
	fmt.Println("🛑 Press Ctrl+C to stop the server")
	
	http.ListenAndServe(":8080", router)
}