import { Link } from "react-router-dom";

export default function NavBar() {
  return (
    <header className="w-full backdrop-blur-lg bg-white/70 sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center">
        <Link
          to="/"
          className="font-semibold text-lg tracking-tight text-gray-800"
        >
           ShopBot
        </Link>
      </div>
    </header>
  );
}