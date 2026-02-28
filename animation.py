class Animation:
    def __init__(self, sp, tr, indices):
        self.sp = sp
        self.tr = tr
        self.tick = 0
        self.images = []
        for i in indices:
            self.images.append(sp.get_image_idx(i))

    def get_image(self):
        i = self.images[(self.tick // self.tr) % len(self.images)]
        self.tick += 1
        return i
