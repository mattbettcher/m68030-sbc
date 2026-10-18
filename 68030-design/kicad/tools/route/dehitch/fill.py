import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1]); f=pcbnew.ZONE_FILLER(b); f.Fill(b.Zones()); b.Save(sys.argv[2]); print('filled')
