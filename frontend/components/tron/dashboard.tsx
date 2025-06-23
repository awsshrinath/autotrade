import Content from "./content"
import Layout from "./layout"
import TradingInterface from "./trading-interface"

export default function Dashboard() {
  return (
    <Layout>
      <div className="space-y-6">
        <Content />
        <TradingInterface />
      </div>
    </Layout>
  )
}
