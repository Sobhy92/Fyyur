#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, flash, redirect, url_for,abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import func
from forms import *
from config import SQLALCHEMY_DATABASE_URI
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
# DONE: connect to a local postgresql database

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
#show is an association table
class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer,db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer,db.ForeignKey('Venue.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)
  venue = db.relationship("Venue", back_populates="venue_relation")
  artist = db.relationship("Artist", back_populates="artist_relation")

class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    venue_relation = db.relationship("Show", back_populates="venue")

# DONE: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    artist_relation = db.relationship("Show", back_populates="artist")



migrate = Migrate(app, db)
# DONE: implement any missing fields, as a database migration using Flask-Migrate
# DONE Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  # DONE: replace with real venues data.
  # #       num_shows should be aggregated based on number of upcoming shows per venue.

  all_places = db.session.query(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  data = []

  for place in all_places:
    place_venues = db.session.query(Venue).filter_by(state=place.state).filter_by(city=place.city).all()
    my_venue = []
    for venue in place_venues:
      upcoming_num = db.session.query(Show).filter(Show.venue_id==venue.id).filter(Show.start_time>datetime.now()).count()
      my_venue.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": upcoming_num
      })
    data.append({
      "city": place.city,
      "state": place.state,
      "venues": my_venue
    })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # DONE: implement search on Venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  data = request.form
  search_writing = data['search_term']

  # make query to get data related the search input
  my_venues = db.session.query(Venue).filter(Venue.name.ilike('%{}%'.format(search_writing))).all()
  response = {}
  response['count'] = len(my_venues)
  response['data'] = my_venues
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # DONE: replace with real venue data from the venues table, using venue_id
  my_venue = db.session.query(Venue).filter(Venue.id == venue_id).one()
  if my_venue:
    #make join to get all shows and their related artists according to given venue_id

    all_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id)
    past_shows = []
    upcoming_shows = []
    current_time = datetime.now()
    for show in all_shows:
      add_show = {
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime('%c')
      }

      #determine if show is past or coming
      if (show.start_time < current_time):
        past_shows.append(add_show)
      else:
        upcoming_shows.append(add_show)

    data = {
      "id": my_venue.id,
      "name": my_venue.name,
      "address": my_venue.address,
      "city": my_venue.city,
      "state": my_venue.state,
      "phone": my_venue.phone,
      "facebook_link": my_venue.facebook_link,
      "image_link": my_venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=data)
  else:
    return render_template('errors/404.html')
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  data = request.form
  name = data['name']
  city = data['city']
  state = data['state']
  address = data['address']
  phone = data['phone']
  image_link = data['image_link']
  facebook_link = data['facebook_link']

  error = False
  try:
    new_venue = Venue(name=name,
                      city=city,
                      state=state,
                      address=address,
                      phone=phone,
                      image_link=image_link,
                      facebook_link=facebook_link,
                      )
    db.session.add(new_venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + name + ' could not be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion

  # on successful db insert, flash success

  # DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # DONE: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    db.session.query(Venue).filter(Venue.id == venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Error! record can not be deleted!')
  else:
    flash('Record was successfully deleted!')
  return None
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  # DONE: replace with real data returned from querying the database


  all_artists = db.session.query(Artist.id, Artist.name)
  data = []
  for artist in all_artists:
    data.append({
      "id": artist[0],
      "name": artist[1]
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  data = request.form
  search_writing = data['search_term']

  #get data from database according to given search value
  my_artists = db.session.query(Artist).filter(Artist.name.ilike('%{}%'.format(search_writing))).all()
  response = {}
  response['count'] = len(my_artists)
  response['data'] = my_artists
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # DONR: replace with real venue data from the venues table, using venue_id
  my_artist = db.session.query(Artist).filter(Artist.id == artist_id).one()
  if my_artist:

    # make join to get all shows and their related venues according to given artist_id
    all_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id)
    past_shows = []
    upcoming_shows = []
    current_time = datetime.now()
    for show in all_shows:
      add_show = {
        "venue_id": show.artist_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%c')
      }

      #determine if show is past or coming
      if (show.start_time < current_time):
        past_shows.append(add_show)
      else:
        upcoming_shows.append(add_show)

    data = {
      "id": my_artist.id,
      "name": my_artist.name,
      "city": my_artist.city,
      "state": my_artist.state,
      "genres": my_artist.genres.replace('{', '').replace('}', '').split(','),
      "phone": my_artist.phone,
      "facebook_link": my_artist.facebook_link,
      "image_link": my_artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=data)
  else:
    return render_template('errors/404.html')

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  #get record that needs to be changed from our database
  my_artist = db.session.query(Artist).filter(Artist.id == artist_id).one()
  if my_artist:
    form.name.data = my_artist.name
    form.city.data = my_artist.city
    form.state.data = my_artist.state
    form.phone.data = my_artist.phone
    form.genres.data = my_artist.genres
    form.facebook_link.data = my_artist.facebook_link
    form.image_link.data = my_artist.image_link
    return render_template('forms/edit_artist.html', form=form, artist=my_artist)
  else:
    return render_template('errors/404.html')
  # DONE: populate form with fields from artist with ID <artist_id>


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # DONE: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  my_artist = db.session.query(Artist).filter(Artist.id == artist_id).one()
  data = request.form
  name = data['name']
  city = data['city']
  state = data['state']
  genres = data.getlist('genres')
  phone = data['phone']
  image_link = data['image_link']
  facebook_link = data['facebook_link']
  error = False

  try:
    #applying changes to the row
    my_artist.name = name,
    my_artist.city = city,
    my_artist.state = state,
    my_artist.phone = phone,
    my_artist.genres = genres,
    my_artist.image_link = image_link,
    my_artist.facebook_link = facebook_link,
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + name + ' could not be updated.')
  else:
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  #get venue record that needs to be changed
  my_venue = db.session.query(Venue).filter(Venue.id == venue_id).one()
  if my_venue:
    form.name.data = my_venue.name
    form.city.data = my_venue.city
    form.state.data = my_venue.state
    form.phone.data = my_venue.phone
    form.address.data = my_venue.address
    form.facebook_link.data = my_venue.facebook_link
    form.image_link.data = my_venue.image_link
    return render_template('forms/edit_venue.html', form=form, venue=my_venue)
  else:
    return render_template('errors/404.html')
  # DONE: populate form with values from venue with ID <venue_id>

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # DONE: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

  my_venue = db.session.query(Venue).filter(Venue.id == venue_id).one()
  data = request.form
  name = data['name']
  city = data['city']
  state = data['state']
  address = data['address']
  phone = data['phone']
  image_link = data['image_link']
  facebook_link = data['facebook_link']
  error = False

  try:
    #updating the values to the defined Venue object
    my_venue.name = name,
    my_venue.city = city,
    my_venue.state = state,
    my_venue.address = address,
    my_venue.phone = phone,
    my_venue.image_link = image_link,
    my_venue.facebook_link = facebook_link,
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Venue ' + name + ' could not be updated.')
  else:
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion

  data = request.form
  name = data['name']
  city = data['city']
  state = data['state']
  phone = data['phone']
  genres = data.getlist('genres')
  image_link = data['image_link']
  facebook_link = data['facebook_link']

  error = False
  try:
    new_artist = Artist(name=name,
                        city=city,
                        state=state,
                        phone=phone,
                        genres=genres,
                        image_link=image_link,
                        facebook_link=facebook_link,
                        )
    db.session.add(new_artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + name + ' could not be listed.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  # on successful db insert, flash success

  # DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # Done: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []

  #query all_shows rows in the Show table
  all_shows = db.session.query(Show.artist_id, Show.venue_id, Show.start_time).all()
  for show in all_shows:

    #get artist row and venue row related to every show
    artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id == show[0]).one()
    venue = db.session.query(Venue.name).filter(Venue.id == show[1]).one()
    data.append({
      "venue_id": show[1],
      "venue_name": venue[0],
      "artist_id": show[0],
      "artist_name": artist[0],
      "artist_image_link": artist[1],
      "start_time": show[2].strftime("%c")
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # DONE: insert form data as a new Show record in the db, instead

  data = request.form
  artist_id = data['artist_id']
  venue_id = data['venue_id']
  start_time = data['start_time']
  error=False
  try:
    new_show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(new_show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Show could not be listed.')
  else:
    flash('Show was successfully listed!')
  return render_template('pages/home.html')

  # on successful db insert, flash success

  # DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/



@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
