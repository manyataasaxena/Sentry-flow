import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  DollarSign,
  AlertTriangle,
  Play,
  RefreshCw,
  Search,
  Shield,
  Server,
  Zap,
  BarChart3,
  Settings,
  LogOut,
  Bell,
  Terminal,
  GitBranch,
  ArrowRight,
  RotateCcw,
  Trash2,
  Download,
  Save,
  Check,
  X,
  Info,
  AlertCircle,
  Lock,
  Database,
  Cpu,
  HardDrive,
  Globe,
  Layers,
  Grid,
  List,
  Maximize2,
  Minimize2,
  ZoomIn,
  ZoomOut,
  Move,
  MousePointer,
  PenTool,
  Palette,
  Ruler,
  Scissors,
  Clipboard,
  ClipboardCheck,
  ClipboardList,
  ClipboardX,
  ClipboardPen,
  FileText,
  Image,
  Video,
  Music,
  Calendar,
  MapPin,
  Mail,
  Phone,
  Map,
  Compass,
  Navigation,
  User,
  Key,
  Wifi,
  WifiOff,
  ChevronRight,
  ChevronDown,
  Filter,
  ArrowLeft,
  Upload,
  Copy,
} from "lucide-react";
import { motion } from "framer-motion";

const kpis = [
  { label: "Runs Today", value: "1,284", trend: "+12%", icon: Activity, color: "text-indigo-400" },
  { label: "Success Rate", value: "96.4%", trend: "+3%", icon: CheckCircle2, color: "text-emerald-400" },
  { label: "Blocked Attacks", value: "37", trend: "+5", icon: Shield, color: "text-amber-400" },
  { label: "Avg / p95 Latency", value: "3.2 / 7.9s", trend: "-0.2s", icon: Clock, color: "text-cyan-400" },
  { label: "Total Cost", value: "$12.40", trend: "-8%", icon: DollarSign, color: "text-rose-400" },
  { label: "Active Runs", value: "3", trend: "+1", icon: RefreshCw, color: "text-violet-400" },
];

const agentNodes = [
  { id: "intake", label: "Intake Guard", x: 100, y: 200, status: "active" },
  { id: "planner", label: "Planner", x: 300, y: 100, status: "active" },
  { id: "approval", label: "Approval Gate", x: 300, y: 300, status: "idle" },
  { id: "worker", label: "Worker", x: 500, y: 200, status: "idle" },
  { id: "verifier", label: "Verifier", x: 700, y: 200, status: "idle" },
  { id: "finalize", label: "Finalize", x: 900, y: 200, status: "idle" },
];

const edges = [
  { from: "intake", to: "planner" },
  { from: "planner", to: "approval" },
  { from: "approval", to: "worker" },
  { from: "worker", to: "verifier" },
  { from: "verifier", to: "finalize" },
];

export default function Index() {
  const [activeTab, setActiveTab] = useState("overview");
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Top Navigation */}
      <nav className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between px-4 py-3 max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
                SentryFlow
              </span>
            </motion.div>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search runs, tools, evals..."
                className="pl-9 w-64"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Button variant="ghost" size="icon">
              <Bell className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon">
              <Settings className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
        {/* Hero / Status Banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="relative overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card to-muted/30 p-6 backdrop-blur-sm"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 to-cyan-500/5" />
          <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold">Orchestration Console</h1>
              <p className="text-muted-foreground mt-1">
                Monitor and govern your multi-agent runs in real time
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="secondary" className="gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                System Healthy
              </Badge>
              <Button className="gap-2">
                <Play className="w-4 h-4" />
                New Run
              </Button>
            </div>
          </div>
        </motion.div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {kpis.map((kpi, index) => (
            <motion.div
              key={kpi.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + index * 0.05 }}
            >
              <Card className="hover:border-indigo-500/30 transition-colors">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{kpi.label}</p>
                      <p className="text-2xl font-bold mt-1">{kpi.value}</p>
                    </div>
                    <div className={`p-2 rounded-lg bg-muted ${kpi.color}`}>
                      <kpi.icon className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="mt-4 flex items-center gap-2 text-sm">
                    <span className={kpi.trend.startsWith("+") ? "text-emerald-400" : "text-rose-400"}>
                      {kpi.trend}
                    </span>
                    <span className="text-muted-foreground">vs last week</span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="runs">Runs</TabsTrigger>
            <TabsTrigger value="tools">Tools</TabsTrigger>
            <TabsTrigger value="evals">Evals</TabsTrigger>
            <TabsTrigger value="system">System</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6 mt-4">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              {/* Agent Graph */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="lg:col-span-2 rounded-2xl border border-border bg-card p-6 backdrop-blur-sm"
              >
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Agent Graph</h2>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="icon">
                      <ZoomIn className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <ZoomOut className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <Maximize2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <div className="relative h-80 rounded-xl bg-muted/30 border border-border overflow-hidden">
                  {/* SVG Edges */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    {edges.map((edge, i) => {
                      const from = agentNodes.find((n) => n.id === edge.from);
                      const to = agentNodes.find((n) => n.id === edge.to);
                      if (!from || !to) return null;
                      return (
                        <motion.line
                          key={i}
                          x1={from.x + 60}
                          y1={from.y + 20}
                          x2={to.x}
                          y2={to.y + 20}
                          stroke="rgba(99, 102, 241, 0.4)"
                          strokeWidth={2}
                          strokeDasharray="6 4"
                          initial={{ pathLength: 0 }}
                          animate={{ pathLength: 1 }}
                          transition={{ duration: 1, delay: 0.5 + i * 0.1 }}
                        />
                      );
                    })}
                  </svg>

                  {/* Nodes */}
                  {agentNodes.map((node, index) => (
                    <motion.div
                      key={node.id}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.3 + index * 0.1 }}
                      className="absolute flex items-center gap-3 px-4 py-3 rounded-xl border bg-card/90 backdrop-blur-sm shadow-sm"
                      style={{ left: node.x, top: node.y }}
                    >
                      <div
                        className={`w-3 h-3 rounded-full ${
                          node.status === "active"
                            ? "bg-indigo-500 animate-pulse"
                            : node.status === "idle"
                            ? "bg-cyan-500"
                            : "bg-muted-foreground"
                        }`}
                      />
                      <span className="text-sm font-medium">{node.label}</span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              {/* Quick Stats */}
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Recent Activity</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="flex items-center gap-3 text-sm">
                        <div className="w-2 h-2 rounded-full bg-indigo-500" />
                        <span className="flex-1">Run #{1000 + i} completed</span>
                        <span className="text-muted-foreground">2m ago</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">System Health</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {[
                      { label: "Postgres", value: 99.9, color: "bg-emerald-500" },
                      { label: "Redis", value: 99.8, color: "bg-emerald-500" },
                      { label: "LLM Primary", value: 98.5, color: "bg-amber-500" },
                    ].map((item) => (
                      <div key={item.label}>
                        <div className="flex justify-between text-sm mb-1">
                          <span>{item.label}</span>
                          <span className="text-muted-foreground">{item.value}%</span>
                        </div>
                        <Progress value={item.value} className="h-2" />
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="runs" className="mt-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Active Runs</CardTitle>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm">
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                  <Button variant="outline" size="sm">
                    <Filter className="w-4 h-4 mr-2" />
                    Filter
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/50">
                      <tr>
                        <th className="text-left p-3 font-medium">Run ID</th>
                        <th className="text-left p-3 font-medium">Task</th>
                        <th className="text-left p-3 font-medium">Status</th>
                        <th className="text-left p-3 font-medium">Intent</th>
                        <th className="text-left p-3 font-medium">Cost</th>
                        <th className="text-left p-3 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[1, 2, 3].map((i) => (
                        <tr key={i} className="border-t">
                          <td className="p-3 font-mono">run-{i}</td>
                          <td className="p-3">Analyze Q3 report</td>
                          <td className="p-3">
                            <Badge variant={i === 1 ? "default" : "secondary"}>
                              {i === 1 ? "Running" : "Pending"}
                            </Badge>
                          </td>
                          <td className="p-3">Research</td>
                          <td className="p-3">$0.42</td>
                          <td className="p-3">
                            <div className="flex items-center gap-2">
                              <Button variant="ghost" size="icon">
                                <RefreshCw className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="icon">
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tools" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Tool Registry</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {["Web Search", "HTTP Fetch", "Calculator", "KB Lookup", "Execute Webhook"].map(
                    (tool, i) => (
                      <div
                        key={tool}
                        className="p-4 rounded-lg border hover:border-indigo-500/30 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-muted">
                              {i === 4 ? (
                                <AlertTriangle className="w-5 h-5 text-amber-500" />
                              ) : (
                                <Zap className="w-5 h-5 text-indigo-400" />
                              )}
                            </div>
                            <div>
                              <p className="font-medium">{tool}</p>
                              <p className="text-xs text-muted-foreground">
                                {i === 4 ? "HIGH RISK" : "Standard"}
                              </p>
                            </div>
                          </div>
                          <Badge variant={i === 4 ? "destructive" : "secondary"}>
                            {i === 4 ? "Restricted" : "Available"}
                          </Badge>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="evals" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Adversarial Eval Suite</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    { label: "Total Cases", value: "60" },
                    { label: "Pass Rate", value: "94.2%" },
                    { label: "Critical Block Rate", value: "100%" },
                  ].map((stat) => (
                    <div key={stat.label} className="p-4 rounded-lg border">
                      <p className="text-sm text-muted-foreground">{stat.label}</p>
                      <p className="text-2xl font-bold mt-1">{stat.value}</p>
                    </div>
                  ))}
                </div>
                <div className="rounded-md border p-4">
                  <p className="text-sm text-muted-foreground mb-2">Recent Eval Results</p>
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="flex items-center justify-between text-sm">
                        <span>Case {i}</span>
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                          <span className="text-emerald-500">Passed</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="system" className="mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Circuit Breakers</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {[
                    { name: "LLM Primary", state: "Closed", failures: 0 },
                    { name: "LLM Fallback", state: "Closed", failures: 0 },
                    { name: "Web Search", state: "Closed", failures: 0 },
                  ].map((breaker) => (
                    <div key={breaker.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-emerald-500" />
                        <span>{breaker.name}</span>
                      </div>
                      <div className="text-right">
                        <p className="text-sm">{breaker.state}</p>
                        <p className="text-xs text-muted-foreground">{breaker.failures} failures</p>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Chaos Mode</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Enable Chaos Engineering</p>
                      <p className="text-sm text-muted-foreground">
                        Simulate failures to test resilience
                      </p>
                    </div>
                    <div className="w-12 h-6 rounded-full bg-muted relative">
                      <div className="w-4 h-4 rounded-full bg-white absolute top-1 left-1 shadow-sm" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}