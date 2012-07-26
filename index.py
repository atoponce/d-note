import web
import view
import config
from view import render

urls = ('/', 'index')
render = web.template.render('templates')

class index:
    def GET(self, url):
        if url == "":
            page_file = 'index'
        page_file = 'notes/%s' %(url)

        try:
            f = open(page_file, 'r')
        except IOError:
            return web.notfound()

        content = f.read()
        return render.page(content)

if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()
    app.internalerror = web.debugerror

