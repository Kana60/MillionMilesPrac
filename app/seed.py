from __future__ import annotations

from typing import List

from .models import ScrapedCar


def seed_cars() -> List[ScrapedCar]:
    # Fallback data so the UI isn't empty if Encar blocks scraping.
    return [
        ScrapedCar(make="Hyundai", model="Avante", year=2021, mileage=42000, price=14500000, image="https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=1400&q=80"),
        ScrapedCar(make="Kia", model="K5", year=2022, mileage=31000, price=21900000, image="https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1400&q=80"),
        ScrapedCar(make="Genesis", model="G70", year=2020, mileage=52000, price=28900000, image="https://images.unsplash.com/photo-1603386329225-868f9b1ee6e9?auto=format&fit=crop&w=1400&q=80"),
        ScrapedCar(make="BMW", model="3 Series", year=2019, mileage=68000, price=29900000, image="https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=1400&q=80"),
        ScrapedCar(make="Mercedes-Benz", model="C-Class", year=2018, mileage=74000, price=31900000, image="https://images.unsplash.com/photo-1525609004556-c46c7d6cf023?auto=format&fit=crop&w=1400&q=80"),
        ScrapedCar(make="Audi", model="A4", year=2019, mileage=61000, price=27900000, image="https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=1400&q=80"),
        ScrapedCar(make="Toyota", model="Camry", year=2021, mileage=38000, price=23900000, image="https://images.unsplash.com/photo-1619767886558-efdc259cde1a?auto=format&fit=crop&w=1400&q=80"),
        ScrapedCar(make="Lexus", model="ES", year=2020, mileage=45000, price=35900000, image="https://images.unsplash.com/photo-1609520505218-7421aa54a3b5?auto=format&fit=crop&w=1400&q=80"),
        ScrapedCar(make="Porsche", model="Macan", year=2018, mileage=59000, price=64900000, image="https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1400&q=80"),
        ScrapedCar(make="Land Rover", model="Range Rover Evoque", year=2019, mileage=62000, price=52900000, image="https://images.unsplash.com/photo-1602407294553-6ac9170b3ed0?auto=format&fit=crop&w=1400&q=80"),
        ScrapedCar(make="Volvo", model="XC60", year=2020, mileage=47000, price=45900000, image="https://images.unsplash.com/photo-1607603750909-408e193868c7?auto=format&fit=crop&w=1400&q=80"),
        ScrapedCar(make="Tesla", model="Model 3", year=2021, mileage=33000, price=39900000, image="https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=1400&q=80"),
    ]
