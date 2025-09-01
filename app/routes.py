from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from .models import Product, Order, OrderItem, User
from .forms import RegistrationForm, LoginForm, ProductForm, CheckoutForm
from . import db
from flask_login import login_user, logout_user, login_required, current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@main_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@main_bp.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, is_seller=form.is_seller.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main_bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('main.index'))
        flash('Invalid email or password.')
    return render_template('login.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# Seller: add product
@main_bp.route('/seller/add-product', methods=['GET','POST'])
@login_required
def add_product():
    if not current_user.is_seller:
        flash('Only sellers can add products.')
        return redirect(url_for('main.index'))
    form = ProductForm()
    if form.validate_on_submit():
        p = Product(
            title=form.title.data,
            description=form.description.data,
            price=float(form.price.data),
            stock=form.stock.data,
            seller_id=current_user.id
        )
        db.session.add(p)
        db.session.commit()
        flash('Product added.')
        return redirect(url_for('main.seller_dashboard'))
    return render_template('add_product.html', form=form)

@main_bp.route('/seller/dashboard')
@login_required
def seller_dashboard():
    if not current_user.is_seller:
        flash('Not a seller.')
        return redirect(url_for('main.index'))
    products = Product.query.filter_by(seller_id=current_user.id).all()
    return render_template('seller_dashboard.html', products=products)

@main_bp.route('/buyer/dashboard')
@login_required
def buyer_dashboard():
    orders = Order.query.filter_by(buyer_id=current_user.id).all()
    return render_template('buyer_dashboard.html', orders=orders)

# Cart (session-based)
@main_bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    qty = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    session['cart'] = cart
    flash('Added to cart.')
    return redirect(url_for('main.view_cart'))

@main_bp.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    items = []
    total = 0
    for pid, qty in cart.items():
        p = Product.query.get(int(pid))
        if p:
            items.append({'product': p, 'quantity': qty, 'subtotal': p.price * qty})
            total += p.price * qty
    return render_template('cart.html', items=items, total=total)

# Checkout (demo: create Order objects; for real payment, integrate Stripe)
@main_bp.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty.')
        return redirect(url_for('main.index'))
    form = CheckoutForm()
    if form.validate_on_submit():
        total = 0
        order = Order(buyer_id=current_user.id, total=0)
        db.session.add(order)
        for pid, qty in cart.items():
            product = Product.query.get(int(pid))
            if product:
                oi = OrderItem(order=order, product_id=product.id, quantity=qty, price=product.price)
                db.session.add(oi)
                total += product.price * qty
        order.total = total
        db.session.commit()
        session.pop('cart', None)
        flash('Order placed (demo). Use Stripe to handle real payments.')
        return redirect(url_for('main.buyer_dashboard'))
    return render_template('checkout.html', form=form)
