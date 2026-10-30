import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk

TILE_BYTES = 32

def checksum(data):
    return sum(int.from_bytes(data[i:i+2].ljust(2,b'\0'), 'big') for i in range(0x200,len(data),2)) & 0xffff

def decode_tile(chunk):
    result=[]
    for b in chunk: result.extend((b>>4,b&15))
    return result

def encode_tile(pixels):
    return bytes((pixels[i]<<4)|pixels[i+1] for i in range(0,64,2))

class Studio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Genesis Graphics Studio — Tile Lab 0.1')
        self.geometry('1100x760')
        self.minsize(850,550)
        self.data=None
        self.path=None
        self.preview=None
        self.offset=tk.StringVar(value='0x200')
        self.cols=tk.IntVar(value=16)
        self.rows=tk.IntVar(value=16)
        self.scale=tk.IntVar(value=3)
        self.status=tk.StringVar(value='Open a Genesis ROM to begin.')
        self.palette=[(i*17,i*17,i*17) for i in range(16)]
        bar=ttk.Frame(self)
        bar.pack(fill='x',padx=8,pady=8)
        for name,fn in [('Open ROM',self.open_rom),('Export PNG',self.export_png),('Reimport PNG',self.import_png),('Save Modified ROM',self.save_rom),('Load Palette (.bin)',self.load_palette)]:
            ttk.Button(bar,text=name,command=fn).pack(side='left',padx=3)
        opts=ttk.Frame(self)
        opts.pack(fill='x',padx=8,pady=5)
        for label,var,width in [('Offset',self.offset,12),('Columns',self.cols,5),('Rows',self.rows,5),('Zoom',self.scale,5)]:
            ttk.Label(opts,text=label).pack(side='left',padx=(8,3))
            ttk.Entry(opts,textvariable=var,width=width).pack(side='left')
        ttk.Button(opts,text='Render Tiles',command=self.render).pack(side='left',padx=8)
        ttk.Button(opts,text='Previous',command=lambda:self.move(-1)).pack(side='left',padx=3)
        ttk.Button(opts,text='Next',command=lambda:self.move(1)).pack(side='left',padx=3)
        body=ttk.Frame(self)
        body.pack(fill='both',expand=True,padx=10,pady=5)
        self.canvas=tk.Canvas(body,bg='#24242b',highlightthickness=0)
        self.canvas.pack(side='left',fill='both',expand=True)
        sx=ttk.Scrollbar(body,orient='horizontal',command=self.canvas.xview)
        sx.pack(side='bottom',fill='x')
        self.canvas.configure(xscrollcommand=sx.set)
        sy=ttk.Scrollbar(body,orient='vertical',command=self.canvas.yview)
        sy.pack(side='right',fill='y')
        self.canvas.configure(yscrollcommand=sy.set)
        ttk.Label(self,textvariable=self.status,anchor='w').pack(fill='x',padx=10,pady=8)
        self.canvas.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-1 if e.delta>0 else 1,'units'))

    def open_rom(self):
        path=filedialog.askopenfilename(filetypes=[('Linear Genesis ROMs','*.md *.bin *.gen'),('All files','*.*')])
        if not path:return
        raw=Path(path).read_bytes()
        if len(raw)<0x200 or raw[0x100:0x104]!=b'SEGA':
            messagebox.showerror('Unsupported ROM','Expected a linear Sega Genesis ROM with SEGA at 0x100. Interleaved .smd ROMs need conversion.')
            return
        self.data=bytearray(raw)
        self.path=path
        self.render()

    def layout(self):
        if self.data is None:raise ValueError('Open a ROM first.')
        start=int(self.offset.get(),0)
        cols=self.cols.get()
        rows=self.rows.get()
        scale=self.scale.get()
        if start<0 or start%32:raise ValueError('Offset must be nonnegative and divisible by 32.')
        if not 1<=cols<=64 or not 1<=rows<=128 or not 1<=scale<=8:
            raise ValueError('Columns 1–64, rows 1–128, zoom 1–8.')
        if start+cols*rows*32>len(self.data):
            raise ValueError('Tile selection extends beyond ROM.')
        return start,cols,rows,scale

    def make_image(self):
        start,cols,rows,_=self.layout()
        img=Image.new('P',(cols*8,rows*8))
        for j in range(cols*rows):
            tile=decode_tile(self.data[start+j*32:start+(j+1)*32])
            x=(j%cols)*8
            y=(j//cols)*8
            for yy in range(8):
                for xx in range(8):
                    img.putpixel((x+xx,y+yy),tile[yy*8+xx])
        palette=[value for color in self.palette for value in color]
        img.putpalette(palette+[0]*(768-len(palette)))
        return img

    def render(self):
        try:
            img=self.make_image()
            start,cols,rows,scale=self.layout()
            shown=img.convert('RGB').resize((img.width*scale,img.height*scale),Image.Resampling.NEAREST)
            self.preview=ImageTk.PhotoImage(shown)
            self.canvas.delete('all')
            self.canvas.create_image(0,0,anchor='nw',image=self.preview)
            self.canvas.config(scrollregion=(0,0,shown.width,shown.height))
            self.status.set(f'Tiles: {cols*rows} | ROM offset: 0x{start:X}–0x{start+cols*rows*32-1:X} | {Path(self.path).name}')
        except Exception as e:messagebox.showerror('Tile view',str(e))

    def move(self,d):
        try:
            self.offset.set(hex(max(0,int(self.offset.get(),0)+d*self.cols.get()*self.rows.get()*32)))
            self.render()
        except Exception as e:messagebox.showerror('Navigation',str(e))

    def export_png(self):
        try:
            img=self.make_image()
            path=filedialog.asksaveasfilename(defaultextension='.png',filetypes=[('PNG','*.png')])
            if path:
                img.save(path)
                self.status.set(f'Exported {path}. Preserve palette indices 0–15.')
        except Exception as e:messagebox.showerror('Export',str(e))

    def import_png(self):
        try:
            start,cols,rows,_=self.layout()
            path=filedialog.askopenfilename(filetypes=[('PNG','*.png')])
            if not path:return
            with Image.open(path) as im:
                if im.size!=(cols*8,rows*8):
                    raise ValueError(f'PNG must be {cols*8}×{rows*8} pixels; got {im.size}.')
                if im.mode=='P':
                    values=list(im.getdata())
                    if any(v>15 for v in values):
                        raise ValueError('Indexed PNG uses indices above 15.')
                else:
                    lookup={color:i for i,color in enumerate(self.palette)}
                    colors=list(im.convert('RGB').getdata())
                    if not set(colors).issubset(lookup):
                        raise ValueError('RGB PNG has colors outside the active 16-color palette.')
                    values=[lookup[c] for c in colors]
            output=bytearray()
            for ty in range(rows):
                for tx in range(cols):
                    tile=[values[(ty*8+y)*(cols*8)+tx*8+x] for y in range(8) for x in range(8)]
                    output.extend(encode_tile(tile))
            if not messagebox.askyesno('Confirm reimport',f'Replace {len(output)} ROM bytes at 0x{start:X}?\nOnly use this on known uncompressed tile regions.'):
                return
            self.data[start:start+len(output)]=output
            self.render()
            self.status.set('Reimport complete; save modified ROM to recalculate checksum.')
        except Exception as e:messagebox.showerror('Reimport',str(e))

    def save_rom(self):
        if self.data is None:
            messagebox.showerror('Save','Open a ROM first.')
            return
        path=filedialog.asksaveasfilename(defaultextension='.md',initialfile=Path(self.path).stem+'-mod.md',filetypes=[('Genesis ROM','*.md *.bin *.gen')])
        if not path:return
        if Path(path).resolve()==Path(self.path).resolve():
            messagebox.showerror('Save','Choose a different file. Original ROM must remain unchanged.')
            return
        out=bytearray(self.data)
        out[0x18e:0x190]=checksum(out).to_bytes(2,'big')
        Path(path).write_bytes(out)
        self.status.set(f'Saved {path} • repaired checksum {checksum(out):04X}.')

    def load_palette(self):
        path=filedialog.askopenfilename(filetypes=[('Binary palette','*.bin'),('All files','*.*')])
        if not path:return
        raw=Path(path).read_bytes()
        if len(raw)!=32:
            messagebox.showerror('Palette','Palette file must contain exactly 32 bytes.')
            return
        self.palette=[]
        for i in range(0,32,2):
            v=int.from_bytes(raw[i:i+2],'big')
            self.palette.append((((v>>1)&7)*255//7,((v>>5)&7)*255//7,((v>>9)&7)*255//7))
        if self.data is not None:self.render()

if __name__=='__main__':
    Studio().mainloop()
