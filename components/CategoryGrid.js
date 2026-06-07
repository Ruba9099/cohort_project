const categories = [
  { title: 'Automatic', img: 'https://images.unsplash.com/photo-1519741491656-7a2f0bf1b4d3?w=800&q=60&auto=format&fit=crop' },
  { title: 'Quartz', img: 'https://images.unsplash.com/photo-1518546305927-5b5d6f0f6d1d?w=800&q=60&auto=format&fit=crop' },
  { title: 'Limited Edition', img: 'https://images.unsplash.com/photo-1509395176047-4a66953fd231?w=800&q=60&auto=format&fit=crop' }
];

export default function CategoryGrid() {
  return (
    <section className="categories container">
      <h2>Explore Categories</h2>
      <div className="grid">
        {categories.map((c) => (
          <div className="card" key={c.title}>
            <img src={c.img} alt={c.title} />
            <div className="overlay">{c.title}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
