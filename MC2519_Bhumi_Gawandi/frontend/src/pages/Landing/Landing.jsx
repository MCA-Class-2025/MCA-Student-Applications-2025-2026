import Navbar from "../../components/Navbar/Navbar";
import Hero from "../../components/Hero/Hero";
import Features from "../../components/Features/Features";
import Footer from "../../components/Footer/Footer";

function Landing() {
  return (
    <div className="bg-[#F6F4EE]">
      <Navbar />
      <Hero />
      <Features />
      <Footer />
    </div>
  );
}

export default Landing;