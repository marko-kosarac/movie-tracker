import bgVideo from "../assets/home-bg.mp4";

function Home() {
  return (
    <div className="home-page">
      
      {/* <video autoPlay muted loop className="background-video">
        <source src={bgVideo} type="video/mp4" />
      </video> */}

      <div className="overlay"></div>

      <div className="hero">
        <h1 className="hero-title">Movie Tracker</h1>
        <p className="hero-text">
          Track, rate and explore your movie universe.
        </p>
      </div>

    </div>
  );
}

export default Home;