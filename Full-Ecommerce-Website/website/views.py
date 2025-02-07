from flask import Blueprint, render_template
from flask import Blueprint, render_template, flash, redirect, request, jsonify
from .models import Product, Cart, Order
from flask_login import login_required, current_user
from . import db



views = Blueprint('views', __name__)

@views.route('/about')
def about():
    return render_template('about.html')



@views.route('/')
@views.route('/home')
def home():

    items = Product.query.filter_by(flash_sale=True)

    return render_template('home.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

@views.route('/add_to_cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    item_to_add = Product.query.get(item_id)
    item_exists = Cart.query.filter_by(product_link=item_id, customer_link=current_user.id).first()
    if item_exists:
        try:
            item_exists.quantity = item_exists.quantity + 1
            db.session.commit()
            flash(f' Quantity of { item_exists.product_in_cart.product_name } has been updated')
            return redirect(request.referrer)
        except Exception as e:
            print('Quantity not Updated', e)
            flash(f'Quantity of { item_exists.product_in_cart.product_name } not updated')
            return redirect(request.referrer)

    new_cart_item = Cart()
    new_cart_item.quantity = 1
    new_cart_item.product_link = item_to_add.id
    new_cart_item.customer_link = current_user.id

    try:
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f'{new_cart_item.product_in_cart.product_name} added to cart')
    except Exception as e:
        print('Item not added to cart', e)
        flash(f'{new_cart_item.product_in_cart.product_name} has not been added to cart')

    return redirect(request.referrer)


@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = 0
    for item in cart:
        amount += item.product_in_cart.current_price * item.quantity

    return render_template('cart.html', cart=cart, amount=amount, total=amount+200)


@views.route('/pluscart')
@login_required
def plus_cart():
    cart_id = request.args.get('cart_id')
    cart_item = Cart.query.get(cart_id)
    try:
        cart_item.quantity += 1
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()
        amount = sum(item.product_in_cart.current_price * item.quantity for item in cart)

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 200  # Shipping fee
        }
        return jsonify(data)
    except Exception as e:
        print("Error updating cart:", e)
        return jsonify({"error": "Failed to update cart."}), 500



@views.route('/minuscart')
@login_required
def minus_cart():
    cart_id = request.args.get('cart_id')
    cart_item = Cart.query.get(cart_id)
    try:
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            db.session.delete(cart_item)
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()
        amount = sum(item.product_in_cart.current_price * item.quantity for item in cart)

        data = {
            'quantity': max(cart_item.quantity, 0),  # Ensure no negative values
            'amount': amount,
            'total': amount + 200  # Shipping fee
        }
        return jsonify(data)
    except Exception as e:
        print("Error updating cart:", e)
        return jsonify({"error": "Failed to update cart."}), 500



@views.route('removecart')
@login_required
def remove_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        
        if cart_item is None:  # Check if cart_item is None
            return jsonify({'error': 'Cart item not found'}), 404
        
        # Store the quantity before deleting the cart item
        quantity = cart_item.quantity
        
        db.session.delete(cart_item)
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product_in_cart.current_price * item.quantity  # Corrected here

        data = {
            'quantity': quantity,  # Use the stored quantity
            'amount': amount,
            'total': amount + 200  # Shipping fee
        }

        return jsonify(data)
    
@views.route('/checkout')
@login_required
def checkout():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = 0
    for item in cart:
        amount += item.product_in_cart.current_price * item.quantity

    return render_template('checkout.html', cart=cart, amount=amount, total=amount+200)



@views.route('/orders')
@login_required
def order():
    orders = Order.query.filter_by(customer_link=current_user.id).all()
    return render_template('orders.html', orders=orders)


@views.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search')
        items = Product.query.filter(Product.product_name.ilike(f'%{search_query}%')).all()
        return render_template('search.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

    return render_template('search.html')




