def hexify(data):
  return ' '.join( [ '%02x' % x for x in list( data ) ] )
