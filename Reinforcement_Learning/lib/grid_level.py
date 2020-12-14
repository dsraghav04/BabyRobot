   
import os
import numpy as np
import random

from ipycanvas import MultiCanvas
from ipycanvas import Canvas, hold_canvas
from ipywidgets import Image
from ipywidgets import Layout
from ipywidgets import Play, IntProgress, HBox, VBox, link

from maze import Maze
from direction import Direction
from arrows import Arrows


'''
  Helper Functions
'''

''' setup all the main components required to animate a grid level '''
def setup_play_level( level, on_update, interval=1000, min=1, max=8 ):
  play = Play(interval=interval, min=min, max=max, step=1)
  progress = IntProgress(min=min, max=max, step=1)

  link((play, 'value'), (progress, 'value'))
  play.observe(on_update, 'value')

  canvas_dimensions = level.get_canvas_dimensions()
  layout = Layout(width=f'{canvas_dimensions[0]}px')
  return play, progress, layout

  
''' class to draw a grid level '''
class GridLevel():
    
  num_canvases = 4        # number of canvases/layers
  cell_pixels = 64        # pixel dimensions of a grid square     
  padding = 2             # padding around the cells
  base_color = 'orange'   # color of the grid base layer
  grid_color = '#777'     # grid line color
  start_color = '#ed1818' # color of start square
  end_color = 'green'     # color of the exit square

  maze = None             # instance of maze if defined
  debug_maze = True       # write the maze to a svg file
  
  save_images = False     # enable writing canvas as an image
  
  def __init__(self, width, height, 
               start = None,
               end = None,
               add_maze = False,
               maze_seed = None,
               add_compass = False, 
               side_panel = False,
               fill_center = False,
               show_start_text = False):
    
    self.width = width
    self.height = height
    self.maze_seed = maze_seed
    self.fill_center = fill_center
    self.add_compass = add_compass
    self.side_panel = side_panel
    self.show_start_text = show_start_text
    
    # calculate other cell values
    self.calculate_dimensions()
    self.calculate_positions()
    
    # arrow draw class
    self.arrows = Arrows(self.cell_pixels,self.padding,length=24,width=7,height=11)
    
    # default start position is top-left
    if not start: self.start = [0,0]
    else: self.start = start
      
    # default end position is bottom-right
    if not end: self.end = [self.width-1,self.height-1]
    else: self.end = end      
    
    self.setup_canvases(add_maze)
    
  '''
    Helper Methods
  '''
  
  def set_center(self,x,y):
    ''' set the center of the tile '''
    self.cx = x + self.center
    self.cy = y + self.center     

  def calculate_positions(self):
    ''' calculate the number of pixels to center of a square '''
    self.center = self.cell_pixels//2 - self.padding    
    
  def calculate_dimensions(self):
    ''' calculate the total dimensions of the canvases '''
    self.width_pixels = self.width * self.cell_pixels
    self.height_pixels = self.height * self.cell_pixels
        
    # add the padding around the level
    self.width_pixels += (self.padding*2)
    self.height_pixels += (self.padding*2)
            
    self.total_width = self.width_pixels
    if self.add_compass or self.side_panel: self.total_width += 100
    self.total_height = self.height_pixels    
    
  '''
    Enquiry Functions
  ''' 
  
  def get_end(self):
    return self.end
  
  def save_to_file(self, file_name):    
    if self.save_images:
      self.canvases.to_file(file_name)   
  
  def get_canvas_dimensions(self):
    return [self.total_width,self.total_height]
                
  '''
    Draw Functions
  '''
  
  def setup_canvases(self,add_maze):        
    self.create_canvases()
    self.draw_level(add_maze)
        
  def draw_level(self,add_maze):        
    self.draw_level_base()
    
    canvas = self.canvases[1]
    with hold_canvas(canvas):     
      self.draw_grid(canvas)
      self.draw_start(canvas)
      self.draw_exit(canvas)
      self.draw_border(canvas)      
      
      if add_maze: self.draw_maze(canvas)
      if self.fill_center: self.draw_non_grid_area( canvas, [1,1], self.width-2, self.height-2 )
      if self.add_compass: self.draw_compass(canvas)             

  def grid_to_pixels_inverse_y( self, grid_pos, xoff = 0, yoff = 0 ):
    x = (grid_pos[0] * self.cell_pixels) + self.padding + xoff
    y = (grid_pos[1] * self.cell_pixels) + self.padding + yoff  
    y = self.height_pixels - ((grid_pos[1] + 1) * self.cell_pixels) - self.padding + yoff    
    return x,y    

  def grid_to_pixels( self, grid_pos, xoff = 0, yoff = 0 ):
    x = (grid_pos[0] * self.cell_pixels) + self.padding + xoff
    y = (grid_pos[1] * self.cell_pixels) + self.padding + yoff   
    return x,y   
  
  def draw_maze(self,canvas):    
    self.maze = Maze(self.width, self.height, self.start[0], self.start[1], seed = self.maze_seed)
    self.maze.make_maze()        
    if self.debug_maze: self.maze.write_svg('maze.svg')

    self.maze.write_to_canvas( canvas,
                               self.height*self.cell_pixels,
                               self.padding)       
  
  def draw_border(self,canvas):
    ''' draw the level border '''
     
    canvas.stroke_style = '#000'
    canvas.line_width = 5
    canvas.set_line_dash([0,0])
    canvas.stroke_rect(self.padding, 
                       self.padding, 
                       self.width_pixels-(2*self.padding),
                       self.height_pixels-(2*self.padding)) 

  def draw_non_grid_area(self, canvas, area_start, width, height ):
    x1,y1 = self.grid_to_pixels_inverse_y( area_start, self.padding, self.padding )
    
    area_end = [area_start[0] + width, area_start[1] - height]    
    x2,y2 = self.grid_to_pixels_inverse_y( area_end, -self.padding, -self.padding )      
    
    canvas.stroke_style = '#000'
    canvas.line_width = 5      
    canvas.fill_style = '#fff'
    canvas.fill_rect(x1,y1,x2-x1,y2-y1)
    canvas.stroke_rect(x1,y1,x2-x1,y2-y1)        
      
      
  def draw_compass(self,canvas):      
    ''' draw the compass '''

    arrows = Arrows(64,2,length=15,width=5,height=11)
    arrows.draw(canvas,
                self.width_pixels + 27, 14,
                [Direction.North,Direction.West,Direction.South,Direction.East],
                center_width = 28 )

    canvas.font = 'bold 20px sans-serif'
    canvas.fill_text(str("W"), self.width_pixels + 13, 52)    
    canvas.fill_text(str("N"), self.width_pixels + 49, 18)     
    canvas.fill_text(str("E"), self.width_pixels + 82, 52)     
    canvas.fill_text(str("S"), self.width_pixels + 51, 85)   
           

  def draw_level_base(self):
    ''' draw the base of the grid '''
    self.draw_rect(0, self.width_pixels, self.height_pixels, self.base_color) 

  def draw_grid(self,canvas):        
    ''' add dashed lines showing grid '''             
    canvas.clear()
    canvas.stroke_style = self.grid_color
    canvas.line_width = 1
    canvas.set_line_dash([4,8])    

    # draw the grid onto the canvas
    for y in range(self.height):   
      for x in range(self.width):   
        canvas.stroke_rect(self.cell_pixels * x + self.padding, 
                           self.cell_pixels * y + self.padding, 
                           self.cell_pixels,
                           self.cell_pixels)
        
  def draw_start(self,canvas):      
    ''' add the start '''
    canvas = self.canvases[1]
    start_x, start_y = self.grid_to_pixels( self.start )
    canvas.fill_style = self.start_color
    canvas.fill_rect(start_x, start_y, self.cell_pixels, self.cell_pixels)       
    canvas.fill_style = '#fff'
    
    if self.show_start_text:
      canvas.text_align = 'left'
      canvas.font = 'bold 17px sans-serif'
      canvas.fill_text(str("START"), start_x + 5, start_y + 38)     
      
  def draw_exit(self, canvas):
    ''' add the exit '''    
    end_x, end_y = self.grid_to_pixels( self.end )
    canvas.fill_style = self.end_color
    canvas.fill_rect(end_x, end_y, self.cell_pixels, self.cell_pixels)    
    canvas.fill_style = '#fff'
    canvas.text_align = 'left'
    canvas.font = 'bold 20px sans-serif'
    canvas.fill_text(str("EXIT"), end_x + 10, end_y + 40)     
        
        
  def create_canvases(self):        
                
    self.canvases = MultiCanvas(n_canvases=self.num_canvases, 
                                width=self.total_width, 
                                height=self.total_height, 
                                sync_image_data=True)               

  def draw_rect(self, canvas_index, width, height, color):
    canvas = self.canvases[canvas_index]
    canvas.fill_style = color
    canvas.fill_rect(0, 0, width, height)              
    
  def show_cell_value( self, row, col, value, color = '#002', back_color = None ):
    ''' display the given value in the specified cell '''   
    self.show_cell_text( row, col, f"{value:0.1f}", color, back_color )
        
  def show_cell_text( self, row, col, value, color = '#002', back_color = None ):
    ''' display the given value in the specified cell '''     
            
    if (self.fill_center == False 
    or not ((row >= 1 and row <= self.height-2) and (col >= 1 and col <= self.width-2))):    
      x,y = self.grid_to_pixels( [col,row], self.padding, self.padding )    
      self.set_center(x,y) # calculate the center of this cell

      canvas = self.canvases[3]
      with hold_canvas(canvas):                
        canvas.clear_rect(self.cx-18,self.cy-18,36,36) 

        if back_color is not None:
          canvas.fill_style = back_color
          canvas.fill_rect(self.cx-18,self.cy-10,36,20)      

        canvas.fill_style = color
        canvas.text_align = 'center'
        canvas.font = 'bold 14px sans-serif'
        canvas.fill_text(f"{value}", self.cx, self.cy+5)    
            
  def show_values(self,values):
    ''' display the cell values on the grid '''
    for row in range(values.shape[0]):
      for col in range(values.shape[1]):
        back_color = "rgba(40,40,40,0.7)"
        color = '#fff'
        if col == self.start[0] and row == self.start[1]: 
          back_color = "rgba(0, 0, 0, 0.6)"          
        if col == self.end[0] and row == self.end[1]:                         
          back_color = "rgba(0, 0, 0, 0.8)"            
        self.show_cell_value( row, col, values[row][col], color, back_color )          
          
  def draw_directions(self, canvas, col, row, directions, color):
    ''' draw arrow in each direction in supplied list '''
    x,y = self.grid_to_pixels( [row,col], self.padding, self.padding )    
    canvas.clear_rect(x,y,self.cell_pixels,self.cell_pixels) 
    self.arrows.draw(canvas,x,y,directions,color)           
          
  def show_cell_directions(self,col,row,directions,color = '#00008b'):    
    canvas = self.canvases[3]
    with hold_canvas(canvas): 
      self.draw_directions(canvas, col, row, directions, color)     
        
  def show_cell_direction_text(self,directions):   
    ''' add a text string to each cell showing the directions '''              
    for row in range(directions.shape[0]):
      for col in range(directions.shape[1]):
        # dont show directions on the exit
        if col != self.end[0] or row != self.end[1]:        
          dir_list = self.get_direction_list(directions,row,col)    
          dir_string = ""
          for direction in dir_list:          
            if direction == Direction.North: dir_string += "N"      
            if direction == Direction.South: dir_string += "S"                  
            if direction == Direction.East:  dir_string += "E"                
            if direction == Direction.West:  dir_string += "W"     

          self.show_cell_text( row, col, dir_string, '#fff',"rgba(40,40,40,0.7)" )         
          
  def get_direction_list(self,directions,row,col):
    ''' convert the direction value into a list of individual directions '''
    dir_list = []
    dir_value = directions[row][col]    
    if dir_value & Direction.North: dir_list.append( Direction.North )
    if dir_value & Direction.South: dir_list.append( Direction.South )
    if dir_value & Direction.East:  dir_list.append( Direction.East ) 
    if dir_value & Direction.West:  dir_list.append( Direction.West )    
    return dir_list
          
  def show_directions(self,directions):   
    ''' display the cell directions given in the supplied array '''
    for row in range(directions.shape[0]):
      for col in range(directions.shape[1]):
        # dont show directions on the exit
        if col != self.end[0] or row != self.end[1]:
          dir_list = self.get_direction_list(directions,row,col)
          self.show_cell_directions(row,col,dir_list,color='#0000cc')
          
  def side_panel_text(self,x,y,text,canvas_id=3,font='bold 14px sans-serif', color='#000'):
    ''' add information text in the side panel '''
    canvas = self.canvases[canvas_id]
    with hold_canvas(canvas): 
      
      canvas.clear_rect(70,70,190,56)      
      canvas.fill_style = color
      canvas.text_align = 'center'
      canvas.font = font
      canvas.fill_text(text, x, y) 