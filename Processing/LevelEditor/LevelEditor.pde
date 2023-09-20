ArrayList<int[]> rects;

int currentPosX;
int currentPosY;

int boundsX;
int boundsY;

int res = 16;

int round(float no, int place)
{
   return floor(no / place) * place; 
}

void setup()
{
  rects = new ArrayList<int[]>();
  size(1280, 720);
}


void draw() {
  
  background(255);
  
  circle(round(mouseX, res), round(mouseY, res), 4);
  
  if (mousePressed)
  {
    noFill();
    rect(round(currentPosX, res), round(currentPosY, res), round(mouseX - currentPosX, res), round(mouseY - currentPosY, res));
  }
  
  fill(0);

  for (int i = 0; i < rects.size(); i++)
  {
    rect(rects.get(i)[0], rects.get(i)[1], rects.get(i)[2], rects.get(i)[3]);
  }
}

void mousePressed()
{
  currentPosX = round(mouseX, res);
  currentPosY = round(mouseY, res);
}

void mouseReleased()
{
  boundsX = round(mouseX - currentPosX, res);
  boundsY = round(mouseY - currentPosY, res);

  rects.add(new int[]{currentPosX, currentPosY, boundsX, boundsY});
  print((rects.size() == 1 ? "" : "|") + currentPosX + " " + currentPosY + " " + boundsX + " " + boundsY);
}
