import { Link } from "react-router-dom";

export default function NavBar() {
  return (
    <header className="w-full py-3 bg-secondary/80 backdrop-blur-md sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 flex items-center">
        <Link to="/" className="font-semibold text-xl text-text">
          retailBot
        </Link>
      </div>
    </header>
  );
}